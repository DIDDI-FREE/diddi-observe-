# Remise DiddiShop — 24 novembre 2026

Référence : [standard universel 2.0.0](../../DIDDI-Observability-v1.md).

## Vérifié côté plateforme

L'incident 502 est rétabli : un secret manquant empêchait le démarrage central.
Les routes HTTPS sont actives, avec authentification dédiée : 401 sans identifiant
ou avec celui d'un autre service ; 200 avec le bon identifiant.
Des logs et traces synthétiques API et worker ont été retrouvés dans Loki et Tempo,
avec les composants distincts conservés. Cela valide la chaîne centrale, pas encore
l'instrumentation de l'application. Les cinq scrapes métier existants sont UP.

## Paramètres à transmettre

```ini
OTEL_SERVICE_NAME=diddishop
ENVIRONMENT=staging
DEPLOYMENT_ID=diddishop-staging
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_LOGS_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=https://logs-otel.diddifree.com/otlp/diddishop
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://logs-otel.diddifree.com/otlp/diddishop/v1/logs
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://logs-otel.diddifree.com/otlp/diddishop/v1/traces
```

Les valeurs privées sont dans `secrets/onboarding/diddishop.env`, hors Git.
OTEL_EXPORTER_OTLP_HEADERS fournit Authorization=Basic <identifiant dédié>.
Un METRICS_BEARER_TOKEN distinct est fourni pour le scrape. Aucun scope OAuth/S2S
métier n'est requis. Ne pas réutiliser de secret métier.
Pas de CA privée, volume partagé ou réseau Docker partagé nécessaire.

Transport : OTLP HTTP/protobuf uniquement, Content-Type application/x-protobuf,
géré par le SDK. Ne pas envoyer un JSON applicatif brut. Ajouter les suffixes
/v1/logs et /v1/traces exactement une fois ; les endpoints spécifiques sont complets.

Le schéma d'événement reste 1.0.0 : timestamp UTC, level, event, message et resource.
Traduire service_name en ressource service.name=diddishop. Fournir namespace=diddi,
version, instance, environnement, déploiement et diddi.component=api/worker/scheduler
selon le processus. Propager traceparent et corréler les véritables trace_id/span_id.
request_id et correlation_id ne remplacent pas les identifiants de trace.

## Retry, limites et confidentialité

Export asynchrone par lots, files bornées, timeout 5 secondes, flush d'arrêt borné.
Backoff exponentiel avec jitter, respect de Retry-After ; reprises sur erreurs réseau
et 429/502/503/504, pas sur 400/401/403/404/413. Compter pertes/rejets, sans bloquer le métier.
Limites configurées : 64 KiB par événement de log, 4 MiB par requête HTTP.
Passerelle : 20 requêtes/seconde par IP, burst 40, partagé entre routes.

Interdits : mots de passe, PIN/OTP, tokens, cookies, clés API, headers d'authentification,
URLs signées, données de paiement sensibles, corps complets de requêtes/réponses.
Téléphones, emails, adresses, positions précises et IP complètes sont exclus par défaut.
Aucune dérogation d'un autre service ne s'applique à cette intégration.

## Travail attendu de l'équipe

1. Transmettre les variables via le Compose aux settings/SDK de chaque processus.
2. Raccorder les vrais loggers ; vérifier niveaux, propagation et absence de doublons.
3. Déployer et fournir SHA réel, contact et marqueurs synthétiques API/worker.
4. Déclarer les URLs joignables des endpoints Prometheus, ports/chemins et composants
   couverts ; installer le token dédié et tester refus/succès. Le scrape DiddiShop
   reste désactivé en attendant ces informations et leur vérification.
5. Vérifier corrélation, données sensibles et panne collecteur sans transaction réelle.

La plateforme activera ensuite le scrape et vérifiera les données de l'application.
La réception synthétique centrale ne vaut pas déclaration de conformité du producteur.
