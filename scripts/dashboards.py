"""Versioned Grafana resources; no provisioning API writes required."""
import json
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
P={'type':'prometheus','uid':'prometheus'}
FILTER='service_name=~"$service",environment=~"$environment"'


def panel(title,expr,kind='timeseries',ds=P,unit='short'):
    result = {'title':title,'type':kind,'datasource':ds,
            'targets':[{'refId':'A','expr':expr,'query':expr,'queryType':'range','legendFormat':'{{service_name}} {{component}}'}],
            'fieldConfig':{'defaults':{'unit':unit,'noValue':'Aucune donnée'},'overrides':[]},
            'options':{'legend':{'displayMode':'list','placement':'bottom'},'reduceOptions':{'calcs':['lastNotNull'],'values':False}}}
    if ds['type']=='tempo':
        result['targets'][0].update(queryType='traceql',tableType='traces')
    if kind=='table' and ds['type']=='prometheus':
        result['targets'][0].update(instant=True,format='table')
    return result


def text(title,content):
    return {'title':title,'type':'text','options':{'mode':'markdown','content':content}}


def write(name,title,panels):
    for i,p in enumerate(panels):
        p.update(id=i+1,gridPos={'x':(i%2)*12,'y':(i//2)*9,'w':12,'h':9})
    queries=[('environment','label_values(diddi_observe_service_info, environment)'),
             ('service','label_values(diddi_observe_service_info{environment=~"$environment"}, service_name)')]
    variables=[{'name':n,'label':n,'type':'query','datasource':P,'query':q,'refresh':1,'includeAll':True,'allValue':'.*','multi':True,'current':{'text':'All','value':'$__all'}} for n,q in queries]
    dashboard={'uid':'diddi-'+name,'title':title,'tags':['diddi','observability-v1'],
               'schemaVersion':39,'version':1,'timezone':'utc','editable':False,
               'time':{'from':'now-1h','to':'now'},'refresh':'30s',
               'templating':{'list':variables},'panels':panels,
               'links':[{'title':'DIDDI dashboards','type':'dashboards','tags':['diddi'],'asDropdown':True,'includeVars':True,'keepTime':True}]}
    path=ROOT/'dashboards'/f'{name}.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(dashboard,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    write('platform','DIDDI · Plateforme',[
        text('Couverture réelle','Les services inventoriés ne sont pas nécessairement raccordés. **Aucune donnée ≠ zéro erreur.** La conformité est déclarée avec preuves dans le registre. Les noms de service et environnements servent de filtres communs.'),
        panel('Services recensés',f'count(diddi_observe_service_info{{{FILTER}}})','stat'),
        panel('Registre de conformité',f'diddi_observe_service_info{{{FILTER}}}','table'),
        panel('Signaux activés',f'diddi_observe_collection_enabled{{{FILTER}}}','table'),
        panel('Disponibilité des sondes',f'probe_success{{{FILTER}}}'),
        panel('Requêtes par seconde',f'sum by (service_name) (rate(diddi_http_server_requests_total{{{FILTER}}}[5m]))','timeseries',unit='reqps'),
        panel('Erreurs serveur par seconde',f'sum by (service_name) (rate(diddi_http_server_requests_total{{{FILTER},status_code=~"5.."}}[5m]))'),
        panel('p95 HTTP',f'histogram_quantile(0.95,sum by (le,service_name) (rate(diddi_http_server_request_duration_seconds_bucket{{{FILTER}}}[5m])))','timeseries',unit='s')])
    write('service','DIDDI · Service',[
        panel('Débit par route',f'sum by (service_name,route) (rate(diddi_http_server_requests_total{{{FILTER}}}[5m]))','timeseries',unit='reqps'),
        panel('Taux de 5xx',f'sum by (service_name) (rate(diddi_http_server_requests_total{{{FILTER},status_code=~"5.."}}[5m])) / sum by (service_name) (rate(diddi_http_server_requests_total{{{FILTER}}}[5m]))','timeseries',unit='percentunit'),
        panel('p95 par route',f'histogram_quantile(0.95,sum by (le,service_name,route) (rate(diddi_http_server_request_duration_seconds_bucket{{{FILTER}}}[5m])))','timeseries',unit='s'),
        panel('Dépendances',f'sum by (service_name,dependency,outcome) (rate(diddi_dependency_requests_total{{{FILTER}}}[5m]))'),
        panel('Scrape applicatif',f'up{{{FILTER},job=~"service-.*"}}'),
        text('SLO','SLO non défini tant que le propriétaire du service ne l’a pas enregistré. Les compteurs de durée legacy permettent une moyenne, pas un p95.')])
    write('logs','DIDDI · Logs',[
        text('Investigation','Filtrer le service et l’environnement. Les liens **Trace** des lignes contenant un trace_id ouvrent Tempo. Une trace peut être absente à cause du sampling. Les logs fichiers utilisent environment ; les logs OTLP utilisent deployment_environment_name.'),
        panel('Logs fichiers', '{service_name=~"$service",environment=~"$environment"}', 'logs',{'type':'loki','uid':'loki'}),
        panel('Logs OTLP', '{service_name=~"$service",deployment_environment_name=~"$environment"}', 'logs',{'type':'loki','uid':'loki'})])
    write('traces','DIDDI · Traces',[
        text('Recherche de traces','Utiliser Explore → Tempo pour chercher par ID, durée ou statut. Les attributs resource.service.name et deployment.environment.name proviennent de l’enregistrement authentifié. Les traces du pilote sont synthétiques.'),
        panel('Traces des services','{ resource.service.name =~ "$service" && resource.deployment.environment.name =~ "$environment" }','table',{'type':'tempo','uid':'tempo'})])
    write('workers','DIDDI · Workers et files',[
        panel('Âge du heartbeat',f'time() - diddi_worker_heartbeat_timestamp_seconds{{{FILTER}}}','timeseries',unit='s'),
        panel('Messages en attente',f'diddi_queue_pending{{{FILTER}}}'),
        panel('Âge du plus ancien message',f'diddi_queue_oldest_age_seconds{{{FILTER}}}','timeseries',unit='s'),
        panel('Dead letters',f'diddi_queue_dead_letter{{{FILTER}}}'),
        panel('Résultats des jobs',f'sum by (service_name,job_type,outcome) (rate(diddi_jobs_total{{{FILTER}}}[5m]))'),
        text('Tâches planifiées','Le seuil de fraîcheur dépend de la cadence. Ne pas appliquer le seuil des workers continus aux jobs quotidiens. Seuils métier à enregistrer avant activation.')])
    write('collector','DIDDI · Santé de la collecte',[
        panel('Composants centraux','up{job=~"observe-.*"}'),
        panel('Mémoire des composants','process_resident_memory_bytes{job=~"observe-.*"}','timeseries',unit='bytes'),
        panel('Spans exportés','sum(rate(otelcol_exporter_sent_spans_total[5m]))'),
        panel('Échecs d’export','sum(rate(otelcol_exporter_send_failed_spans_total[5m]))'),
        panel('Échantillons par cible','scrape_samples_scraped'),
        panel('Pertes déclarées par les services','sum by (service_name,signal,reason) (rate(diddi_telemetry_dropped_total[5m]))'),
        text('Stockage','Volumes persistants locaux, rétention staging. Les quotas disque et l’espace libre de l’hôte doivent être surveillés avant production ; aucun accès hôte n’est activé automatiquement.')])
    sources={'apiVersion':1,'datasources':[
        {'name':'Prometheus','uid':'prometheus','type':'prometheus','access':'proxy','url':'http://prometheus:9090','isDefault':True,'editable':False},
        {'name':'Loki','uid':'loki','type':'loki','access':'proxy','url':'http://loki:3100','editable':False,
         'jsonData':{'derivedFields':[{'name':'Trace','datasourceUid':'tempo','matcherRegex':'"trace_id"\\s*:\\s*"([0-9a-f]{32})"','url':'$${__value.raw}','urlDisplayLabel':'Ouvrir la trace'}]}},
        {'name':'Tempo','uid':'tempo','type':'tempo','access':'proxy','url':'http://tempo:3200','editable':False,
         'jsonData':{'tracesToLogsV2':{'datasourceUid':'loki','spanStartTimeShift':'-5m','spanEndTimeShift':'5m','filterByTraceID':True,'filterBySpanID':False,'tags':[{'key':'service.name','value':'service_name'}]}}}]}
    files={'datasources/sources.yaml':sources,'dashboards/provider.yaml':{'apiVersion':1,'providers':[{'name':'DIDDI','folder':'DIDDI','type':'file','disableDeletion':False,'updateIntervalSeconds':30,'allowUiUpdates':False,'options':{'path':'/var/lib/grafana/dashboards'}}]}}
    rules=[]
    specs=[('target-down','Cible inaccessible','up == 0','2m'),
           ('readiness-down','Service indisponible','probe_success == 0','2m'),
           ('telemetry-loss','Perte de télémétrie','sum by (service_name,environment) (rate(diddi_telemetry_dropped_total[5m])) > 0','5m'),
           ('missing-scrape','Source métriques absente','diddi_observe_collection_enabled{signal="metrics"} == 1 unless on(service_name,environment,deployment_id,component) up{job=~"service-.*"}','2m')]
    for uid,title,expr,duration in specs:
        rules.append({'uid':uid,'title':title,'condition':'B','for':duration,'noDataState':'OK','execErrState':'Error',
                      'annotations':{'summary':title,'runbook_url':'https://github.com/DIDDI-FREE/diddi-observe-/blob/main/docs/RUNBOOK.md'},
                      'labels':{'severity':'warning','owner':'diddi-observe'},
                      'data':[{'refId':'A','relativeTimeRange':{'from':300,'to':0},'datasourceUid':'prometheus',
                               'model':{'refId':'A','expr':expr,'instant':True,'range':False,'intervalMs':1000,'maxDataPoints':43200}},
                              {'refId':'B','relativeTimeRange':{'from':0,'to':0},'datasourceUid':'__expr__',
                               'model':{'refId':'B','type':'threshold','expression':'A','conditions':[{'evaluator':{'type':'gt','params':[-1]},'operator':{'type':'and'},'reducer':{'type':'last'},'type':'query'}]}}]})
    # Expressions return only offending series (including zero); threshold > -1.
    files['alerting/rules.yaml']={'apiVersion':1,'groups':[{'orgId':1,'name':'DIDDI technical','folder':'DIDDI','interval':'1m','rules':rules}]}
    files['alerting/routing.yaml']={'apiVersion':1,'contactPoints':[{'orgId':1,'name':'local-only','receivers':[{'uid':'local-audit-sink','type':'webhook','settings':{'url':'http://registry:9108/alerts','httpMethod':'POST'}}]}],
                                   'policies':[{'orgId':1,'receiver':'local-only','group_by':['grafana_folder','alertname'],'group_wait':'30s','group_interval':'5m','repeat_interval':'4h'}]}
    for name,data in files.items():
        path=ROOT/'config/grafana'/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(yaml.safe_dump(data,sort_keys=False,allow_unicode=True),encoding='utf-8')


if __name__=='__main__':main()
