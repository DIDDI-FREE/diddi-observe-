# DiddiGo — raccordement à DiddiObserve

Service canonique `diddigo`, environnement `staging`, déploiement `diddigo-staging`. Lire [la remise commune](TEAM-HANDOFF.md) et [le contrat JSON](teams/diddigo.json).

## État observé le 17 novembre 2026

Stack Portainer `diddi-go-backend` (15), application saine ; révision Git indiquée par Portainer `a84c27bf7655c28b4b945d47f14e06426577e6aa` (ce champ seul ne prouve pas le contenu de l'image). Aucune variable OTEL ou METRICS dans le conteneur inspecté.

Dans le dépôt local : `app_base/core/observability.py` écrit des événements JSON sur le logger `uvicorn.error`, avec corrélation request_id. `app_base/main.py` expose `/health`, `/ready` et `/metrics`. La fonction `/metrics` inspectée ne vérifie pas de token. Aucun exporteur OpenTelemetry trouvé dans les sources et dépendances recherchées. Ce constat porte sur le checkout local, pas une preuve du contenu de l'image distante.

## Activation centrale vérifiée

Routes logs/traces activées le 17 novembre 2026. Tests POST : sans identifiant 401, identifiant dédié valide 200, sur HTTP `http://169.58.70.37:19480` et HTTPS `https://logs-otel.diddifree.com`, certificat vérifié avec le magasin standard. Le 404 à la racine est normal ; ce n'est pas un dashboard. Les modules restent raccordés par adresse publique, aucun réseau Docker partagé requis.

Dernier redéploiement DiddiGo vérifié : révision Portainer `fa5e069087f801d6d3529f935e3399f9974efffb`, conteneurs healthy. Les variables OTEL/METRICS sont enregistrées dans la stack, mais absentes du conteneur app. Le checkout local de même SHA ne les référence pas dans `docker-compose.portainer.yml` et ne contient pas l'export OTLP recherché. Aucun log ni trace diddigo trouvé sur les 15 dernières minutes lors de cette vérification. L'équipe doit encore réaliser les changements ci-dessous ; redéployer sans eux ne suffit pas.

## Paramètres du module

Les règles d'implémentation et de validation sont exclusivement celles du [protocole universel, section 2](../DIDDI-Observability-v1.md#2-architecture-et-transports).

| Paramètre | Valeur |
| --- | --- |
| Service | `diddigo` |
| Environnement | `staging` |
| Déploiement | `diddigo-staging` |
| Base OTLP fournie | `http://169.58.70.37:19480/otlp/diddigo` |
| Endpoint logs | `http://169.58.70.37:19480/otlp/diddigo/v1/logs` |
| Alternative HTTPS | Même chemin sur `https://logs-otel.diddifree.com` |
| Métriques | `/metrics`, scrape central désactivé |
| Transport logs retenu | OTLP HTTP/protobuf |
| Secrets | `secrets/onboarding/diddigo.env`, hors Git |

Noms communs à implémenter : ceux de la section 2.2 du protocole. Écart constaté : passage des variables dans le Compose et exporteurs encore manquants dans la révision inspectée. Aucun log ni trace du producteur validé à ce stade. Le contact et le SHA après correction restent à fournir.

[Contrat JSON](teams/diddigo.json). Cette fiche est un diagnostic et un jeu de paramètres, pas un protocole spécifique à DiddiGo.
