> Mise à jour MVP v1.1.3 : utiliser le HTTP public par IP sans attendre HTTPS. Les consignes HTTPS ci-dessous sont historiques ; la configuration actuelle est dans [MIGRATION-V1.md](teams/MIGRATION-V1.md).

# Paramètres centraux DiddiSend et DiddiFree ID

Ce profil prépare uniquement `diddisend` et `diddifree-id` en staging. Les routes sont provisionnées ; cela ne certifie pas que les producteurs exportent leurs données. Le registre reste `inventoried`. Le pilote synthétique reste disponible.

## Remise aux équipes : HTTPS public, sans CA privée

**Décision du 17 novembre 2026 :** utiliser le HTTPS public géré par Nginx Proxy Manager. Aucun fichier de CA privée ni certificat client à installer dans ID ou Send. Les clients conservent la vérification TLS avec leur magasin standard de confiance.

Le domaine d'ingestion n'est pas encore défini/configuré dans cette remise. Les routes centrales existent, mais leur publication via NPM reste à réaliser et vérifier. Les fichiers JSON utilisent une URL nulle ; les fichiers `.env` gardent les exports OTLP désactivés jusqu'à confirmation du domaine.

- [Migration précise de DiddiFree ID et DiddiSend](teams/MIGRATION-V1.md).
- [Contrat de remise ID, sans secrets](teams/diddifree-id.json).
- [Contrat de remise Send, sans secrets](teams/diddisend.json).

Deux secrets indépendants par module sont conservés : identifiants Basic d'ingestion et token Bearer de scrape. Les fichiers locaux `secrets/onboarding/diddifree-id.env` et `secrets/onboarding/diddisend.env` ont été ajustés sans rotation des secrets et sans afficher leurs valeurs. Ne transmettre que le fichier du module concerné, par canal sécurisé ; ne pas transmettre les fichiers d'administration centrale ou les clés privées.

Les réseaux privés déjà raccordés servent aux probes et futurs scrapes. Les équipes utiliseront l'URL HTTPS publique confirmée pour OTLP ; elles ne doivent plus copier le nom Docker ou l'IP directe du déploiement historique comme nouvelle URL d'export.

## Historique TLS central du 16 novembre — pas un prérequis équipe

Le certificat privé existant et `docs/certs/diddi-observe-staging-ca.pem` sont conservés pour l'exploitation et les tests du point d'entrée direct historique. Le certificat serveur expire le 14 février 2027 à 15:04 UTC. Cette documentation ne le retire ni ne le renouvelle et ne configure pas NPM. Le nouveau point d'entrée public doit être vérifié avant de remplacer les URLs des producteurs.

## Métriques, santé et logs

Les probes privés de readiness sont activés. Les cibles métriques privées sont préparées dans `config/onboarding/services.json` mais désactivées jusqu'à confirmation de l'installation du nouveau token : `/internal/metrics` pour Send et `/metrics` pour ID. Après confirmation, activer uniquement ces entrées, régénérer les fichiers et redéployer DiddiObserve. Ne pas déclarer de métriques disponibles avant `up=1`.

Les routes OTLP logs sont disponibles ; aucun montage de logs historiques ni accès au socket Docker n'est créé. L'exception temporaire OTP en clair est maintenue côté producteur, conformément à la décision utilisateur. Sa présence dans les logs centraux dépend des événements que l'équipe choisit d'exporter ; la plateforme ne certifie pas leur anonymisation. Aucun OTP réel ne doit être utilisé pour le test de raccordement.

## Déploiement et retour arrière

`OBSERVE_PILOT_PREFIX=onboarding-`, `COMPOSE_PROFILES=synthetic`, `OBSERVE_SOURCE_NETWORKS_EXTERNAL=true`, `OBSERVE_ID_NETWORK=diddi-auth_default`, `OBSERVE_SEND_NETWORK=diddisend-backend_default` sélectionnent le profil distant. Les valeurs TLS et dictionnaires de secrets sont installés à l'exécution par Portainer, jamais dans les images.

Le profil par défaut garde le registre réel désactivé ; sans variables distantes, le Compose Portainer crée deux réseaux locaux de test. Les changements de profil doivent conserver les volumes. Pour revenir au pilote seul, rétablir le commit et les variables sauvegardés dans le dossier de secrets ; ne pas supprimer les données Grafana, Loki, Prometheus ou Tempo.

Le profil `onboarding-` utilise les noms de conteneurs complets `diddi-observe-<service>-1` pour éviter les collisions avec les services Alloy/Prometheus déjà présents chez les producteurs. Ce profil distant suppose donc le nom de projet Compose `diddi-observe`.

## Vérification du 16 novembre 2026

- Déploiement confirmé par Portainer au commit `b95fc8760c1ce3386b501c848aa92454582e300b` ; neuf services centraux en fonctionnement et initialisation terminée avec code 0.
- Douze contrôles des routes OTLP : quatre acceptations avec le bon identifiant, quatre refus sans authentification et quatre refus avec l'identifiant de l'autre service. Enveloppes vides uniquement : ce test ne simule pas des événements métier des producteurs.
- Vérification TLS stricte réussie sur l'IP publique et vérification du nom privé dans le certificat (TLS 1.3). Aucun contournement de validation du certificat.
- Pilote synthétique complet réussi à 15:10:55 UTC : métriques, logs fichier et OTLP, trace Tempo, identité imposée, filtrage d'attributs et corrélation. Trace : `318a8d255c6814ae08eaa388c2d5ab28`.
- Six dashboards provisionnés et quatre règles évaluées sans erreur. Les dix cibles de scrape sont accessibles, dont les six composants centraux.
- Readiness privée ID à `1`. Readiness Send à `0`, API indiquée `unhealthy` par Docker ; alerte `readiness-down` déclenchée pour `diddisend`. Aucune modification de Send effectuée. Réception de notifications locales confirmée dans le registre ; aucun canal externe configuré.
- À 15:15:45 UTC, l'alerte transitoire sur l'ancienne cible Alloy est résolue après expiration de sa série dans la fenêtre Prometheus. Seule l'alerte de readiness DiddiSend reste active.

Rapports locaux sans secrets : `test-results/onboarding-verification.json` et `test-results/smoke.json`. L'arrivée de véritables logs/traces des deux producteurs et leurs métriques reste à valider après installation des paramètres par chaque équipe. Les dossiers de secrets sont exclus de Git et du contexte Docker ; les accès Windows au dossier de remise sont limités à l'utilisateur courant et SYSTEM.
