# DiddiGo — raccordement à DiddiObserve

Service canonique `diddigo`, environnement `staging`, déploiement `diddigo-staging`. Lire [la remise commune](TEAM-HANDOFF.md) et [le contrat JSON](teams/diddigo.json).

## État observé le 17 novembre 2026

Stack Portainer `diddi-go-backend` (15), application saine ; révision Git indiquée par Portainer `a84c27bf7655c28b4b945d47f14e06426577e6aa` (ce champ seul ne prouve pas le contenu de l'image). Aucune variable OTEL ou METRICS dans le conteneur inspecté.

Dans le dépôt local : `app_base/core/observability.py` écrit des événements JSON sur le logger `uvicorn.error`, avec corrélation request_id. `app_base/main.py` expose `/health`, `/ready` et `/metrics`. La fonction `/metrics` inspectée ne vérifie pas de token. Aucun exporteur OpenTelemetry trouvé dans les sources et dépendances recherchées. Ce constat porte sur le checkout local, pas une preuve du contenu de l'image distante.

## Activation centrale en attente

Les adresses ci-dessous sont réservées à DiddiGo et ses identifiants dédiés sont générés. La connexion Portainer s'est fermée avant activation des routes ; celles-ci ne sont pas encore déployées ni testées. DiddiObserve doit ajouter les identifiants à la configuration centrale, activer les routes diddigo dans le profil onboarding, redéployer sa stack et vérifier POST sans/mauvais/bon identifiant (401/401/200). L'équipe peut implémenter le raccordement dès maintenant, mais doit attendre cette validation pour activer les exports. Ce point ne dépend ni de HTTPS ni d'un réseau partagé.

## Travail demandé à l'équipe DiddiGo

Ajouter une couche d'export OTLP HTTP/protobuf pour les logs et traces, sans réécrire les opérations métier. Brancher les événements existants dans le pipeline de logs sans doubler les handlers ; conserver la console. Instrumenter les requêtes FastAPI et les appels sortants, propager traceparent et corréler trace_id/span_id/request_id. Déclarer service.name=diddigo, deployment.environment.name=staging, deployment_id=diddigo-staging et la version réellement déployée. Conserver le schéma central et les champs métier utiles.

Prendre en charge les variables ci-dessous dans les settings **et** dans le Compose réellement utilisé par Portainer. Ces noms sont le contrat à implémenter, pas des variables déjà fonctionnelles dans le code inspecté. L'endpoint générique doit recevoir exactement une fois le suffixe `/v1/traces` pour les traces. L'endpoint logs est déjà complet.

```ini
ENVIRONMENT=staging
DEPLOYMENT_ID=diddigo-staging
OTEL_EXPORTER_OTLP_ENDPOINT=http://169.58.70.37:19480/otlp/diddigo
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://169.58.70.37:19480/otlp/diddigo/v1/logs
OTEL_LOGS_ENABLED=true
OTEL_EXPORTER_OTLP_CA_FILE=
OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE_FILE=
OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE=
```

Copier `OTEL_EXPORTER_OTLP_HEADERS` et `METRICS_BEARER_TOKEN` depuis le fichier privé remis pour **diddigo**. Ne pas utiliser ceux de DiddiSend. Ne pas changer aveuglément APP_ENV, qui peut contrôler d'autres comportements métier : ajouter la traduction explicite de l'environnement de télémétrie.

Protéger `/metrics` par `Authorization: Bearer <METRICS_BEARER_TOKEN>` : secret absent => 503 ; header absent/faux => 401 ou 403 ; bon secret => 200 au format Prometheus. Ne pas utiliser une clé utilisateur ou métier. Le scrape central reste désactivé jusqu'à vérification.

Prévoir exports en arrière-plan par lots, délais bornés, files bornées, arrêt propre et désactivation explicite. Une indisponibilité de DiddiObserve ne bloque pas l'API. Ne pas exporter de mots de passe, cookies ou tokens.

## Validation à retourner

Tests : absence/mauvais/bon token métriques, export des logs et traces, absence de doublons, panne de collecteur sans panne métier. Après déploiement, fournir SHA réel et contact responsable, faire une requête de test non destructive et communiquer son request_id/trace_id. DiddiObserve vérifie les événements reçus dans Loki et Tempo avant de déclarer le module raccordé.

Aucun montage de CA, aucun volume de logs partagé ni réseau Docker commun n'est nécessaire pour cet export. Les changements du dépôt et de la stack DiddiGo sont à réaliser par son équipe.
