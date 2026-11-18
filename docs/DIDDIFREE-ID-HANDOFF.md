> État actualisé du 18 novembre : voir [METRICS-STATUS.md](METRICS-STATUS.md). Les diagnostics antérieurs ci-dessous sont historiques ; les JSON de remise sont actualisés.

# Fiche DiddiFree ID

Source normative : [protocole universel v1.2.1](../DIDDI-Observability-v1.md). Cette fiche décrit uniquement les paramètres et les écarts connus.

- Service : `diddifree-id` ; environnement : `staging` ; déploiement : `diddifree-id-staging`.
- Traces : `http://169.58.70.37:19480/otlp/diddifree-id/v1/traces` ; HTTPS disponible avec le même chemin sur `https://logs-otel.diddifree.com`.
- Alias historiques : `METRICS_AUTH_TOKEN`, `DIDDI_DEPLOYMENT_ID`, interrupteur `OTEL_ENABLED`, endpoint complet `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`.
- Logs : fichier `/var/log/diddifree/observability.jsonl` sur volume `diddifree-id-observability-logs-staging`. Rotation côté producteur ; montage collecteur en lecture seule et prise en charge JSONL encore à activer/valider côté central.
- Secrets : `secrets/onboarding/diddifree-id.env`, hors Git.
- État : routes centrales disponibles ; réception réelle des traces et collecte fichier non validées. Scrape métriques central désactivé. SHA réellement exécuté et contact à confirmer.
- Politique OTP temporaire inchangée ; aucune modification par cette révision documentaire.

[Paramètres JSON](teams/diddifree-id.json) · [Correspondances de migration](teams/MIGRATION-V1.md).
