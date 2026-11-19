# Remise commune aux équipes — protocole 2.0.0

Référence normative unique : [protocole universel DIDDI](../DIDDI-Observability-v1.md).
Le nom de fichier historique est conservé pour ne pas casser les liens ; la version normative est 2.0.0.

Tous les modules applicatifs existants et nouveaux utilisent **OTLP HTTP/protobuf pour les logs et traces** et **scrape Prometheus authentifié pour les métriques**. Aucune alternative par volume partagé, collecte stdout ou gRPC n'est conforme pour les applications DIDDI. Les copies locales de dépannage restent possibles sans collecte centrale.

Les paramètres varient par service, jamais les règles. Les JSON sont des configurations cibles sans secrets, pas des preuves de conformité. Ne pas remplacer un secret installé par un champ vide.

| Module | Paramètres | État observé / action |
| --- | --- | --- |
| DiddiSend | [JSON](teams/diddisend.json) | Logs/traces OTLP et métriques reçus ; vérifier la checklist 2.0.0 |
| DiddiGo | [JSON](teams/diddigo.json) | Logs/traces OTLP et métriques reçus ; vérifier la checklist 2.0.0 |
| DiddiPay | [JSON](teams/diddipay.json) | Métriques UP ; OTLP préparé, activation centrale en attente — [suivi](teams/DIDDIPAY-ONBOARDING.md) |
| DiddiFreeID | [JSON](teams/diddifree-id.json) | Traces/métriques reçues, logs worker reçus par fichier ; migration OTLP logs requise |

[Message de migration DiddiFreeID](teams/DIDDIFREE-ID-MIGRATION-OTLP.md).
[Migration commune](teams/MIGRATION-V1.md).
[État opérationnel historique](METRICS-STATUS.md).

La conformité exige réception réelle de chaque signal applicable et validation séparée API/worker, identité correcte, absence de doublons, respect des règles de données et fonctionnement du métier en cas de panne de collecte.
La publication ne modifie aucun déploiement, secret, montage ou délai de conservation.
