> État actualisé du 18 novembre : voir [METRICS-STATUS.md](METRICS-STATUS.md). Les diagnostics antérieurs ci-dessous sont historiques ; les JSON de remise sont actualisés.

# Remise commune aux équipes

**Source normative unique : [protocole universel DIDDI Observability v1.2.1](../DIDDI-Observability-v1.md).**

Toutes les équipes suivent sa section 2 pour les transports, les variables, l'implémentation et la validation, ainsi que les sections suivantes pour les formats, métriques, traces et alertes. Il n'existe pas de protocole propre à DiddiGo ou DiddiSend.

Les fiches ci-dessous complètent le protocole avec l'identité, les paramètres, les correspondances de variables historiques et l'état de chaque module. Leurs secrets sont transmis séparément et ne sont jamais versionnés.

| Module | Fiche | Paramètres JSON | Dernier état vérifié le 17 novembre 2026 |
| --- | --- | --- | --- |
| DiddiSend | [Fiche](DIDDISEND-HANDOFF.md) | [JSON](teams/diddisend.json) | Logs et traces reçus ; scrape métriques activé le 18 novembre 2026 |
| DiddiGo | [Fiche](DIDDIGO-HANDOFF.md) | [JSON](teams/diddigo.json) | Routes HTTP/HTTPS prêtes ; exporteur et passage Compose à implémenter |
| DiddiFree ID | [Fiche](DIDDIFREE-ID-HANDOFF.md) | [JSON](teams/diddifree-id.json) | Profil fichier conservé ; collecte JSONL centrale et réception de traces non validées |

[Migration des intégrations existantes](teams/MIGRATION-V1.md). Publier ces documents ne modifie ni ne redéploie les modules.

## Vérification demandée à toutes les équipes — v1.2.1

Appliquer le test de raccordement des loggers décrit en section 2.3.1 du protocole. Vérifier le chemin réel des événements jusqu’au handler/exporteur, les niveaux, filtres et propagations avec la configuration du serveur déployé. Corriger seulement les intégrations qui échouent à ce test ; conserver celles dont les logs arrivent déjà correctement sans doublons. Aucun changement de token ou d’URL requis.
