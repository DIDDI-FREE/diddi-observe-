# Raccordement DiddiFree ID : vérification du 13 novembre 2026

Statut : **non connecté**. Inspection en lecture seule de la stack `diddi-auth` (18), environnement Portainer `diddifree-prod`. Aucun changement dans le module.

## Résultats

- API Docker healthy ; `/health/live` répond 200 (`ok`), `/health/ready` répond 200 (`ready`).
- `/metrics` sans authentification répond 503 ; `METRICS_AUTH_TOKEN` est vide dans le conteneur.
- `OTEL_ENABLED=false`, endpoint des traces et en-têtes OTLP vides.
- Identité déployée incohérente : `ENVIRONMENT=staging`, `DIDDI_DEPLOYMENT_ID=diddifree-id-production`.
- `OTP_LOG_PLAINTEXT=true`. Le manifeste local indique que cette option autorise le code OTP et le destinataire dans les logs. Aucun contenu de log sensible n'a été collecté pour ce diagnostic.
- Révision annoncée par Portainer : `c541f6de9541989382ef801767d751e71b8642dc` ; HEAD local : `cfcd55396552051850399dc0b18d424131f533ec`. Le manifeste et l'instrumentation sont commités localement, mais cela ne prouve pas leur présence dans l'image distante.

## Instructions actuelles — remplacent la remise du 13 novembre

Les constats ci-dessus sont historiques, pas un état du déploiement du jour. Pour les équipes, utiliser désormais [la migration v1 sans CA privée](teams/MIGRATION-V1.md) et [les paramètres centraux actualisés](ONBOARDING-READY.md). Le domaine NPM est encore à confirmer ; aucun endpoint d'exemple ne doit être activé. Les secrets existants sont conservés, les variables de CA privée sont vidées et les exports OTLP restent en attente de l'URL publique vérifiée.
