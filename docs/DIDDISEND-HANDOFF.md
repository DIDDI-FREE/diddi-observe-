# Premier raccordement réel : DiddiSend

Statut au 13 novembre 2026 : **préparation, non connecté**. Aucun changement effectué dans le dépôt ou la stack DiddiSend. Aucune source réelle activée dans DiddiObserve.

## Constats vérifiés

- Portainer : environnement `diddifree-prod`, stack `diddisend-backend` (24), conteneur API en fonctionnement et healthy.
- Révision Git annoncée par Portainer : `85f954d8b7ee9b65e1c748893b938ca35853ac29`. Ce champ n'est pas une attestation du contenu de l'image.
- `METRICS_BEARER_TOKEN` et `OTEL_EXPORTER_OTLP_ENDPOINT` sont vides dans le conteneur.
- Lectures HTTP ponctuelles : `/health` et `/ready` répondent 200 avec `status=ok` ; `/internal/metrics` répond 503. Ces lectures ne valident pas la sémantique de readiness du nouveau code.
- Le checkout local DiddiSend est à `8c6341633787a5f7837a193cf468cd6ceddb707a`, avec des modifications non commitées dans l'instrumentation et le Compose. Le manifeste `deploy/observability/diddisend-observability.v1.yaml` est également non suivi. Ne pas considérer ces fichiers comme déployés.
- Le code local prévoit des métriques canoniques, des traces OTLP et des logs JSON stdout. Il ne configure pas un exporteur OTLP de logs. Activer les traces seul ne fera pas arriver les logs dans Loki.

## Message à transmettre au responsable DiddiSend

> Nous démarrons ton raccordement à DiddiObserve. Finalise et teste les changements d'observabilité déjà présents dans ton checkout, puis publie une révision identifiée et déploie-la par ton circuit habituel. Préserve les autres changements en cours ; ne fais pas de commit global du checkout.
>
> Confirme le responsable opérationnel et l'environnement réel. Identité proposée pour le staging : `SERVICE_NAME=diddisend`, `ENVIRONMENT=staging`, `DEPLOYMENT_ID=diddisend-staging`, `OBSERVABILITY_COMPONENT=api`, `OBSERVABILITY_VERSION=1.0.0`, `SERVICE_VERSION=<SHA réellement déployé>`.
>
> Fais passer les variables ci-dessous de Portainer au conteneur API par `services.api.environment`. Les ajouter seulement dans Portainer ne suffit pas si le Compose ne les référence pas.
>
> Configure un token de scrape dédié dans `METRICS_BEARER_TOKEN` et partage-le avec le responsable DiddiObserve par le canal de secrets convenu. N'utilise aucun secret métier. Il sera installé côté central dans l'entrée `diddisend` de `METRICS_TOKENS_JSON`, en conservant les autres entrées.
>
> Après confirmation que la route centrale est activée, configure `OTEL_EXPORTER_OTLP_ENDPOINT=https://169.58.70.37:19443/otlp/diddisend` et `OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64 de diddisend:mot-de-passe-ingestion>`. Le mot de passe d'ingestion est distinct du token métriques et sera fourni par DiddiObserve. Cette URL est la cible prévue, pas une route déjà activée.
>
> Le certificat central actuel est autosigné. Installe le certificat de confiance fourni par la plateforme et configure le client OTLP pour le vérifier ; valide aussi la correspondance de son nom/IP. Ne désactive pas la vérification TLS dans le service.
>
> Pour les logs, ajoute un export OTLP HTTP avec filtrage à la source vers `/otlp/diddisend/v1/logs`, ou propose un fichier JSON avec rotation et volume partagé en lecture seule côté collecteur. Fournis le mécanisme et les tests : stdout seul n'est pas collecté par la stack centrale actuelle. Aucun accès global au socket Docker n'est requis.
>
> Fournis le SHA déployé, le manifeste, le contact, les résultats des tests et les références de secrets sans leurs valeurs. Vérifie `/ready`, le refus de `/internal/metrics` sans token et son succès avec le bon token. Nous validerons ensuite ensemble l'arrivée des trois signaux sur une requête technique sans opération métier.

## Préparation côté DiddiObserve après retour du module

1. Confirmer propriétaire, environnement et révision. Conserver `state=inventoried` jusqu'aux preuves d'ingestion.
2. Préparer une connexion privée persistante : seuls Prometheus et Blackbox de DiddiObserve rejoignent le réseau existant `diddisend-backend_default`, déclaré `external`. Utiliser le nom de conteneur distinct `diddisend-backend-api-1:8000`, pas l'alias générique `api`. Valider sa résolution depuis les collecteurs. Aucun conteneur DiddiSend n'a à être déplacé ou redémarré pour ce branchement côté collecteur.
3. Activer dans le registre les métriques sur `http://diddisend-backend-api-1:8000/internal/metrics` et la santé sur `http://diddisend-backend-api-1:8000/ready`, avec `isolated_network=true`, après validation du réseau et du token. Ne pas scrapper le port public en HTTP avec un secret.
4. Activer la route OTLP du registre, créer le secret d'ingestion et compléter les dictionnaires Portainer sans remplacer les identifiants du pilote. Régénérer les profils standard et synthétique. Ne pas activer la source fichier si le producteur utilise OTLP logs.
5. Tester les configurations et le Compose, adapter le garde-fou des services désactivés à la seule cible autorisée, puis déployer uniquement DiddiObserve.
6. Vérifier `up=1`, `probe_success=1`, métriques canoniques, logs Loki et traces Tempo portant la même identité. Corréler une requête technique connue et vérifier le masquage des données sensibles avant `connected`.

Les trois signaux et leur corrélation restent à valider. Un HTTP 200 de readiness ne certifie pas les dépendances : le nouveau code local autorise également un état `degraded` avec HTTP 200. Les métriques de dépendances devront compléter cette vue. Ne pas annoncer `conformant-v1` avant les contrôles du protocole.
