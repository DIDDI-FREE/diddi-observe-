# Paramètres centraux DiddiSend et DiddiFree ID

Ce profil prépare uniquement `diddisend` et `diddifree-id` en staging. Les routes sont provisionnées ; cela ne certifie pas que les producteurs exportent leurs données. Le registre reste `inventoried`. Le pilote synthétique reste disponible.

## Adresses privées

| Service | Traces OTLP HTTP | Logs OTLP HTTP |
| --- | --- | --- |
| DiddiSend | `https://diddi-observe-gateway-1:8443/otlp/diddisend/v1/traces` | `https://diddi-observe-gateway-1:8443/otlp/diddisend/v1/logs` |
| DiddiFree ID | `https://diddi-observe-gateway-1:8443/otlp/diddifree-id/v1/traces` | `https://diddi-observe-gateway-1:8443/otlp/diddifree-id/v1/logs` |

La passerelle rejoint les réseaux existants `diddisend-backend_default` et `diddi-auth_default`. Seuls la passerelle, Prometheus et Blackbox rejoignent ces réseaux. Les autres backends d'observabilité restent sur leur réseau interne ; aucun nouveau port hôte n'est publié. Ces réseaux partagés ne constituent pas une isolation par service : l'authentification reste obligatoire.

Les URLs publiques temporaires utilisent `https://169.58.70.37:19443` avec les mêmes chemins. Préférer les URLs privées depuis les modules. Ne pas exposer Alloy directement.

## Secrets et TLS

Deux secrets indépendants par module : un mot de passe d'ingestion Basic et un token Bearer de scrape. Ils ne sont pas dérivés de secrets métier. Les paramètres à remettre séparément aux équipes sont générés localement dans `secrets/onboarding/diddisend.env` et `secrets/onboarding/diddifree-id.env`, exclus de Git. Ne pas transmettre `central-env.json`, `previous-env.json`, `auth.json` ou les clés privées aux équipes.

Le certificat public de confiance est [diddi-observe-staging-ca.pem](certs/diddi-observe-staging-ca.pem). Empreinte SHA-256 : `97f51b7163ee2d970f0be0634f2bff25475620fcf4092eb4156c8ba04e58f128`. Le certificat serveur couvre `diddi-observe-gateway-1` et `169.58.70.37` et expire le **14 février 2027 à 15:04 UTC**. La CA expire un an après sa création. Renouveler le serveur avant expiration ; sa clé et la clé CA restent côté plateforme.

Chaque équipe doit intégrer ce certificat public dans son image ou un volume de configuration, à `/etc/diddi-observe/ca.pem`, puis utiliser la variable de confiance indiquée dans son fichier de paramètres. La vérification TLS doit rester activée. Importer le certificat dans le navigateur est une opération distincte de la configuration des SDK.

Les variables Portainer doivent être référencées dans `services.<module>.environment` pour atteindre le conteneur. Ajouter le fichier de confiance et déployer le module reste la responsabilité de son équipe.

## Métriques, santé et logs

Les probes privés de readiness sont activés. Les cibles métriques privées sont préparées dans `config/onboarding/services.json` mais désactivées jusqu'à confirmation de l'installation du nouveau token : `/internal/metrics` pour Send et `/metrics` pour ID. Après confirmation, activer uniquement ces entrées, régénérer les fichiers et redéployer DiddiObserve. Ne pas déclarer de métriques disponibles avant `up=1`.

Les routes OTLP logs sont disponibles ; aucun montage de logs historiques ni accès au socket Docker n'est créé. L'exception temporaire OTP en clair est maintenue côté producteur, conformément à la décision utilisateur. Sa présence dans les logs centraux dépend des événements que l'équipe choisit d'exporter ; la plateforme ne certifie pas leur anonymisation. Aucun OTP réel ne doit être utilisé pour le test de raccordement.

## Déploiement et retour arrière

`OBSERVE_PILOT_PREFIX=onboarding-`, `COMPOSE_PROFILES=synthetic`, `OBSERVE_SOURCE_NETWORKS_EXTERNAL=true`, `OBSERVE_ID_NETWORK=diddi-auth_default`, `OBSERVE_SEND_NETWORK=diddisend-backend_default` sélectionnent le profil distant. Les valeurs TLS et dictionnaires de secrets sont installés à l'exécution par Portainer, jamais dans les images.

Le profil par défaut garde le registre réel désactivé ; sans variables distantes, le Compose Portainer crée deux réseaux locaux de test. Les changements de profil doivent conserver les volumes. Pour revenir au pilote seul, rétablir le commit et les variables sauvegardés dans le dossier de secrets ; ne pas supprimer les données Grafana, Loki, Prometheus ou Tempo.
