# Migration v1.1.3 — MVP HTTP public par IP

HTTPS ne bloque plus la mise en service. La passerelle reçoit les exports sur `http://169.58.70.37:19480`, depuis Internet. Le port public 19480 est redirigé vers le port 8080 de la passerelle. Les identifiants dédiés restent identiques ; aucune CA ni certificat client à monter. Cette connexion HTTP ne chiffre pas le trafic ni les identifiants en transit. Le passage à HTTPS viendra ensuite.

## DiddiSend

Conserver `METRICS_BEARER_TOKEN` et `OTEL_EXPORTER_OTLP_HEADERS` déjà installés. Dans Portainer, définir :

```ini
ENVIRONMENT=staging
DEPLOYMENT_ID=diddisend-staging
OTEL_EXPORTER_OTLP_ENDPOINT=http://169.58.70.37:19480/otlp/diddisend
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://169.58.70.37:19480/otlp/diddisend/v1/logs
OTEL_LOGS_ENABLED=true
OTEL_EXPORTER_OTLP_CA_FILE=
OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE_FILE=
OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE=
```

Redéployer DiddiSend pour appliquer les variables. Conserver les logs OTLP existants, sans migration vers un fichier partagé. La passerelle DiddiObserve est raccordée à `diddisend-backend_default`. Aucun changement métier requis.

## DiddiFree ID

Conserver `METRICS_AUTH_TOKEN` et `OTEL_EXPORTER_OTLP_HEADERS`. Définir :

```ini
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://169.58.70.37:19480/otlp/diddifree-id/v1/traces
OTEL_EXPORTER_OTLP_CERTIFICATE=
```

Redéployer les processus exporteurs. La passerelle est raccordée à `diddi-auth_default`. Conserver le transport fichier JSONL, son volume et sa rotation ; le montage et la règle JSONL du collecteur central restent à activer séparément. Ne pas modifier `OTP_LOG_PLAINTEXT` dans cette migration.

## Vérification

Vérifier le refus sans identifiant, le succès avec l'identifiant dédié, puis la réception effective des données dans Loki et Tempo. Une route opérationnelle ne prouve pas qu'un producteur exporte. Le scrape des métriques est activé séparément après validation du token. Les JSON publics contiennent des champs secrets vides : ne pas effacer les secrets installés. Les fichiers privés `.env` conservent les valeurs existantes.

Le schéma des événements reste 1.0.0. La révision 1.1.3 remplace les consignes précédentes demandant d'attendre un domaine HTTPS. Les autres modules restent sous la responsabilité de leurs équipes ; DiddiObserve ne redéploie que sa propre stack.
