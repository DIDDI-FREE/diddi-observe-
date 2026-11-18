# DiddiSend — configuration validée

Le 17 novembre 2026, après redéploiement : API healthy, 20 entrées de logs retrouvées dans Loki et 4 traces DiddiSend dans Tempo. Cela valide logs et traces ; le scrape central des métriques a été activé le 18 novembre 2026.

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

Conserver les identifiants OTLP et le token métriques déjà installés. Aucun certificat ni réseau partagé requis pour l'ingestion publique. Ne pas imposer de migration des logs vers un fichier.

[Remise commune](TEAM-HANDOFF.md) · [Contrat JSON](teams/diddisend.json) · [Migration](teams/MIGRATION-V1.md).

Vérification du 18 novembre 2026 à 11:42 UTC : cible `service-diddisend` UP, scrape de `/internal/metrics` sans erreur ; 482 séries reçues sous 21 noms de métriques `diddi_*` (les histogrammes produisent plusieurs noms et séries). Secret valide => 200 ; absent/faux => 403. Cela ne garantit pas que chaque famille métier possède déjà des observations.
