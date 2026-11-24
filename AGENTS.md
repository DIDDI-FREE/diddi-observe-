# Instructions du projet DiddiObserve

## Portainer : accès et périmètre persistants

- Le connecteur MCP Portainer est configuré. Le découvrir et l'utiliser en priorité pour toute inspection ou intervention Portainer ; ne pas demander à l'utilisateur de rappeler son existence ou de recopier des informations accessibles par ce connecteur.
- Utiliser le serveur MCP `portainer` destiné à DIDDI, pas `portainer_alphamotors`.
- Lire `get_guidance` avant une nouvelle investigation et retrouver l'environnement `diddifree-prod` par son nom. Ne pas supposer que les identifiants historiques sont immuables.
- Autorisation persistante : lecture des autres stacks/services ; écriture uniquement dans la stack d'observabilité `diddi-observe`. Ne pas modifier les modules métier, réseaux globaux ou reverse proxy d'une autre stack sans autorisation explicite.
- Avant de déclarer l'accès indisponible, redécouvrir les outils disponibles et effectuer un appel de lecture approprié s'il est exposé. Distinguer : outil absent de cette session, erreur du connecteur, refus d'autorisation et panne du service distant. Une erreur antérieure ne prouve pas une panne actuelle.
- Une consigne persistante ne garantit pas la disponibilité technique du connecteur. Rapporter l'erreur réellement observée, sans demander de réinstaller un connecteur simplement parce qu'un appel a échoué.
- Projeter les réponses avec `select`, ne jamais afficher les secrets, préserver les variables existantes lors des mises à jour et vérifier les mutations par une lecture indépendante.

## Standard et documentation

- Le protocole d'observabilité est un standard indépendant des modules : aucun nom de module, adresse réelle, état de déploiement ou diagnostic nominatif dans le document normatif.
- Conserver paramètres, secrets, migrations et états opérationnels dans des documents distincts. Les secrets restent hors Git.
- Logs et traces applicatifs : OTLP HTTP/protobuf. Métriques : scrape Prometheus authentifié. Ne pas créer de variante de transport pour un nouveau module.
- Ne jamais confondre configuration préparée, route disponible, données effectivement reçues et conformité démontrée.
