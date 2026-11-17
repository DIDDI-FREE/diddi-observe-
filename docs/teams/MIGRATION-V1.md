# Migration des modules v1 vers HTTPS public — 17 novembre 2026

Le schéma JSON reste **1.0.0**, les noms de métriques et les chemins `/otlp/<service>/v1/...` ne changent pas. Aucun SDK à remplacer, aucune logique métier à réécrire. La révision documentaire du protocole est **1.1.1**.

## État actuel et répartition

La passerelle directe avec CA privée a été testée le 16 novembre. La nouvelle entrée HTTPS via Nginx Proxy Manager **n'est pas encore configurée ni validée** : aucun domaine réel n'est fourni dans cette remise. Les JSON utilisent `base_url: null`. Ne pas copier une URL d'exemple comme si elle fonctionnait.

DiddiObserve doit configurer DNS/domaine, certificat public et routage Nginx Proxy Manager vers la passerelle centrale authentifiée, préserver le chemin et l'en-tête Authorization, vérifier les refus 401 et l'ingestion autorisée depuis les réseaux des modules. Ne pas pointer directement vers Alloy et contourner l'authentification. Le transport entre NPM et la passerelle est une responsabilité centrale, sans CA à monter dans les modules.

Les fichiers privés `secrets/onboarding/diddifree-id.env` et `diddisend.env` ont été ajustés **sans changer les tokens ni les identifiants OTLP**. Ils désactivent temporairement les exports OTLP et vident les chemins de certificats spécifiques. Copier les valeurs vers les variables de la stack correspondante en conservant les autres variables. Les JSON publics ne contiennent aucun secret : leurs champs secrets vides ne doivent pas effacer les secrets déjà installés.

## DiddiFree ID : changements à appliquer

1. Conserver le même `METRICS_AUTH_TOKEN` et le même `OTEL_EXPORTER_OTLP_HEADERS`. Aucun changement de logique d'authentification `/metrics`.
2. Pour l'instant : `OTEL_ENABLED=false`, `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=` et `OTEL_EXPORTER_OTLP_CERTIFICATE=`. La collecte fichier et les métriques sont indépendantes de cet export.
3. Retirer uniquement le montage/import de CA ajouté pour DiddiObserve dans les conteneurs `app` et `account-purger`, s'il existe et n'est utilisé par aucune autre connexion. Ne pas enlever le magasin standard de certificats de l'image. La variable de CA peut rester dans le Compose avec une valeur vide.
4. Conserver `ENVIRONMENT=staging`, `DIDDI_DEPLOYMENT_ID=diddifree-id-staging` et renseigner la version réellement déployée ainsi que le contact. Ne pas changer la version du schéma des logs.
5. Conserver le transport de logs choisi : `OBSERVABILITY_LOG_FILE=/var/log/diddifree/observability.jsonl`, volume `diddifree-id-observability-logs-staging`, rotation et droits du producteur. Vérifier le modèle d'écriture API/worker : deux handlers indépendants ne doivent pas faire tourner le même fichier. Le montage Alloy et sa règle `.jsonl` restent à activer côté central.
6. Une fois le domaine validé : définir `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://<domaine-confirmé>/otlp/diddifree-id/v1/traces` puis `OTEL_ENABLED=true`. Laisser `OTEL_EXPORTER_OTLP_CERTIFICATE` vide pour utiliser les autorités publiques standard. Redéployer les processus qui exportent réellement des traces.

Ne pas modifier `OTP_LOG_PLAINTEXT` dans cette migration : la décision temporaire et sa portée restent distinctes du choix HTTPS.

## DiddiSend : changements à appliquer

1. Conserver `METRICS_BEARER_TOKEN` et `OTEL_EXPORTER_OTLP_HEADERS` sans rotation. Utiliser `ENVIRONMENT=staging` et `DEPLOYMENT_ID=diddisend-staging`.
2. En attendant le domaine : vider `OTEL_EXPORTER_OTLP_ENDPOINT` et `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`, mettre `OTEL_LOGS_ENABLED=false`. Le code local inspecté active ses exporteurs à partir de ces endpoints ; ne pas supposer qu'une variable `OTEL_ENABLED` propre à ID fonctionne pour Send.
3. Vider `OTEL_EXPORTER_OTLP_CA_FILE`, `OTEL_EXPORTER_OTLP_CLIENT_CERTIFICATE_FILE` et `OTEL_EXPORTER_OTLP_CLIENT_KEY_FILE` pour DiddiObserve. Aucun certificat client n'est requis. Retirer uniquement les montages spécifiques devenus inutiles, sans toucher aux certificats d'autres intégrations.
4. Après validation du domaine : `OTEL_EXPORTER_OTLP_ENDPOINT=https://<domaine-confirmé>/otlp/diddisend`, `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://<domaine-confirmé>/otlp/diddisend/v1/logs`, `OTEL_LOGS_ENABLED=true`. Le SDK ajoute `/v1/traces` à l'endpoint générique : ne pas le doubler.
5. Conserver les logs OTLP déjà implémentés ; aucune migration forcée vers un fichier partagé. Si l'équipe choisit ensuite le fichier, coordonner ce changement et désactiver l'export OTLP des mêmes logs pour éviter les doublons.

## Vérifications après redéploiement

- Confirmer le SHA réel, les variables reçues et le contact, sans publier les secrets.
- `/metrics` (ID) ou `/internal/metrics` (Send) : refus avec token absent/faux, succès avec le bon token. Ne pas confondre activation du token et activation du scrape central.
- Tester l'HTTPS du domaine confirmé depuis le conteneur, avec le magasin de confiance standard. Si l'image n'a aucun certificat racine public, corriger le paquet standard de l'image ; ne pas désactiver TLS et ne pas réinstaller la CA privée pour ce domaine.
- Vérifier les traces et logs réellement reçus et corrélés avant de déclarer le module connecté. Aucun contournement `insecure`, `verify=false` ou équivalent.

Les endpoints et certificats directs historiques restent une affaire interne à la plateforme pendant la transition. Les remplacer dans les documents de remise n'a pas encore modifié le serveur, NPM ou les modules.
