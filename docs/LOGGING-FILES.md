# Collecte fichier historique — retirée du protocole cible

Ce document ne doit plus être transmis comme guide d'implémentation.
Le [protocole universel 2.0.0](../DIDDI-Observability-v1.md) impose OTLP HTTP/protobuf pour les logs et traces applicatifs.

DiddiFreeID utilise encore transitoirement les fichiers actifs observability-api.jsonl et observability-worker.jsonl, montés en lecture seule dans Alloy depuis diddifree-id-observability-logs-staging.
Les positions persistent dans alloy-data ; les archives ne sont pas sélectionnées.
Ne pas retirer cette collecte avant une bascule coordonnée vers OTLP, ni créer de nouvelle intégration par fichiers.

Voir la [migration universelle](teams/MIGRATION-V1.md), le [message DiddiFreeID](teams/DIDDIFREE-ID-MIGRATION-OTLP.md) et l'[état opérationnel](METRICS-STATUS.md).
Les anciennes instructions restent accessibles dans l'historique Git, sans valeur normative actuelle.
