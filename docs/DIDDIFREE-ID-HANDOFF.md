# Raccordement DiddiFree ID : vérification du 13 novembre 2026

Statut : **non connecté**. Inspection en lecture seule de la stack `diddi-auth` (18), environnement Portainer `diddifree-prod`. Aucun changement dans le module.

## Résultats

- API Docker healthy ; `/health/live` répond 200 (`ok`), `/health/ready` répond 200 (`ready`).
- `/metrics` sans authentification répond 503 ; `METRICS_AUTH_TOKEN` est vide dans le conteneur.
- `OTEL_ENABLED=false`, endpoint des traces et en-têtes OTLP vides.
- Identité déployée incohérente : `ENVIRONMENT=staging`, `DIDDI_DEPLOYMENT_ID=diddifree-id-production`.
- `OTP_LOG_PLAINTEXT=true`. Le manifeste local indique que cette option autorise le code OTP et le destinataire dans les logs. Aucun contenu de log sensible n'a été collecté pour ce diagnostic.
- Révision annoncée par Portainer : `c541f6de9541989382ef801767d751e71b8642dc` ; HEAD local : `cfcd55396552051850399dc0b18d424131f533ec`. Le manifeste et l'instrumentation sont commités localement, mais cela ne prouve pas leur présence dans l'image distante.

## Message à transmettre au responsable ID

> Prépare le raccordement DiddiObserve de l'API DiddiFree ID. Confirme le contact opérationnel et le SHA réellement déployé, puis vérifie que la version déployée inclut le manifeste `observability/diddifree-id.observability.v1.yaml` et son instrumentation.
>
> Pour ce staging, utilise `ENVIRONMENT=staging`, `DIDDI_DEPLOYMENT_ID=diddifree-id-staging`, `SERVICE_VERSION=<SHA déployé>`. Configure un `METRICS_AUTH_TOKEN` dédié et partage-le par le canal de secrets convenu pour le scrape central. Ne publie pas sa valeur dans Git ou dans un ticket.
>
> Après confirmation de l'activation de la route centrale, configure `OTEL_ENABLED=true`, `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://169.58.70.37:19443/otlp/diddifree-id/v1/traces` et `OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <base64 de diddifree-id:secret-ingestion>`. Le secret d'ingestion sera fourni côté observabilité et doit être différent du token métriques. La route n'est pas encore activée. Le certificat central est actuellement autosigné : installer sa confiance et vérifier son identité, sans désactiver TLS.
>
> Désactive `OTP_LOG_PLAINTEXT` avant toute collecte centrale. Teste que les codes OTP et destinataires ne sont plus exposés dans les événements collectés. Ne transfère pas rétroactivement des logs contenant ces données.
>
> Fournis un transport de logs compatible : export OTLP HTTP vers `/otlp/diddifree-id/v1/logs`, ou fichier JSON rotatif partagé en lecture seule avec le collecteur. La collecte stdout locale existante ne prouve pas l'arrivée dans le Loki central. Aucun socket Docker global ne doit être ajouté à DiddiObserve.
>
> Vérifie le refus de `/metrics` sans token et son succès avec le bon token, puis communique les preuves, le manifeste et le contact. Ne déclenche pas de véritable envoi OTP pour le test central : utiliser une requête technique sans effet métier.

## Suite côté DiddiObserve

Après préparation du module : ajouter uniquement les collecteurs Prometheus et Blackbox au réseau existant `diddi-auth_default` via une déclaration Compose externe persistante. Vérifier la résolution de `diddi-auth-app-1:8000`. Prévoir le scrape privé `/metrics` et la sonde `/health/ready`, les identités confirmées et les secrets dédiés. Ne pas transmettre le token via le port HTTP public.

Activer la route d'ingestion et les sources uniquement après validation du propriétaire, des secrets et du transport de logs. Régénérer et tester les profils, déployer uniquement DiddiObserve, puis vérifier métriques, logs et traces corrélés avant de déclarer `connected`. Le worker `account-purger` nécessite sa propre validation ; la santé de l'API ne la remplace pas.
