> Mise à jour MVP v1.1.2 : utiliser le HTTP privé Docker sans attendre HTTPS. Les consignes HTTPS ci-dessous sont historiques ; la configuration actuelle est dans [MIGRATION-V1.md](teams/MIGRATION-V1.md).

# Premier raccordement réel : DiddiSend

Statut au 13 novembre 2026 : **préparation, non connecté**. Aucun changement effectué dans le dépôt ou la stack DiddiSend. Aucune source réelle activée dans DiddiObserve.

## Constats vérifiés

- Portainer : environnement `diddifree-prod`, stack `diddisend-backend` (24), conteneur API en fonctionnement et healthy.
- Révision Git annoncée par Portainer : `85f954d8b7ee9b65e1c748893b938ca35853ac29`. Ce champ n'est pas une attestation du contenu de l'image.
- `METRICS_BEARER_TOKEN` et `OTEL_EXPORTER_OTLP_ENDPOINT` sont vides dans le conteneur.
- Lectures HTTP ponctuelles : `/health` et `/ready` répondent 200 avec `status=ok` ; `/internal/metrics` répond 503. Ces lectures ne valident pas la sémantique de readiness du nouveau code.
- Le checkout local DiddiSend est à `8c6341633787a5f7837a193cf468cd6ceddb707a`, avec des modifications non commitées dans l'instrumentation et le Compose. Le manifeste `deploy/observability/diddisend-observability.v1.yaml` est également non suivi. Ne pas considérer ces fichiers comme déployés.
- Le code local prévoit des métriques canoniques, des traces OTLP et des logs JSON stdout. Il ne configure pas un exporteur OTLP de logs. Activer les traces seul ne fera pas arriver les logs dans Loki.

## Instructions actuelles — remplacent la remise du 13 novembre

Les constats ci-dessus sont historiques, pas un état du déploiement du jour. Pour les équipes, utiliser désormais [la migration v1 sans CA privée](teams/MIGRATION-V1.md) et [les paramètres centraux actualisés](ONBOARDING-READY.md). Le domaine NPM est encore à confirmer ; aucun endpoint d'exemple ne doit être activé. Les secrets existants sont conservés, les variables de CA privée sont vidées et les exports OTLP restent en attente de l'URL publique vérifiée.
