# DIDDI Observability — protocole universel

**Version : 2.0.0 — 18 novembre 2026**
**Statut : contrat rédigé, prêt pour adoption et mise en œuvre. Aucune conformité des services ni aucun déploiement ne sont acquis par sa publication.**

Ce protocole définit comment les services DIDDI produisent, transmettent et exploitent leurs logs, métriques, traces et informations de santé dans une plateforme commune, désignée **DiddiObserve**. Il s’applique aux API, workers, tâches planifiées et collecteurs, quel que soit leur langage.

Il s’appuie sur l’[audit des services du 13 novembre 2026](docs/AUDIT.md). Les obligations ci-dessous sont des décisions du contrat DIDDI ; les standards externes utilisés sont référencés en fin de document. Les valeurs initiales de collecte et de rétention sont des paramètres de départ, pas un dimensionnement validé de l’infrastructure actuelle.

## 1. Portée et responsabilités

**DOIT** indique une obligation ; **DEVRAIT** une recommandation dont l’écart doit être expliqué ; **PEUT** une option.

- Le responsable du service DOIT fournir l’instrumentation, protéger les données à la source, maintenir son manifeste et démontrer sa conformité.
- Le responsable DiddiObserve DOIT assurer collecte, normalisation, stockage, accès, tableaux de bord, alertes et suivi de la collecte elle-même.
- Les responsables métier définissent les SLO et les événements métier utiles. Les logs techniques ne remplacent ni les transactions, ni les journaux d’audit, ni le reporting financier.
- Les bases, caches et composants tiers peuvent conserver leur format natif. Leur collecteur DOIT les identifier et leur appliquer un profil `infrastructure`, distinct de la conformité applicative.
- Les interfaces web statiques relèvent d’un profil `web-edge` : santé HTTP, logs du serveur et disponibilité. Elles ne sont pas tenues d’inventer des traces métier.

**Limite opérationnelle de cette mission :** écriture autorisée sur la stack `diddi-observe` ; les autres modules restent en lecture seule pour l'équipe centrale. Leurs responsables appliquent les adaptations dans leurs propres dépôts et stacks. La publication de ce contrat ne modifie ni ne redéploie automatiquement aucun module.

## 2. Architecture et transports

```text
Services et workers DIDDI
  ├─ logs structurés → OTLP HTTP/protobuf → Alloy → Loki
  ├─ endpoint métriques authentifié ← Prometheus
  └─ traces OTLP → collecteur → stockage de traces
                                      ↓
                  Grafana : plateforme, service, opération
```

La référence cible utilise Grafana, Prometheus, Loki et un collecteur compatible OpenTelemetry. Alloy est une option cohérente avec l’existant. Le stockage de traces peut être Tempo ou Jaeger : les producteurs DOIVENT utiliser OTLP afin de rester indépendants de ce choix.

Les services NE DOIVENT PAS appeler les API métier d’autres services pour alimenter les tableaux de bord techniques. Des sondes de santé bornées et des métriques sur les appels métier réellement exécutés sont autorisées.

| Signal | Transport de référence | Règle |
| --- | --- | --- |
| Logs applicatifs | OTLP HTTP/protobuf obligatoire | Une seule chaîne centrale par événement ; stdout seul n'active aucune collecte |
| Métriques | Scrape HTTP(S), exposition Prometheus/OpenMetrics | Cible joignable par Prometheus et authentifiée, déclarée dans le manifeste |
| Traces | OTLP HTTP/protobuf | Adresse publique configurable et authentifiée ; HTTPS ou exception HTTP MVP décrite en section 2.1 |
| Santé | GET HTTP(S), réponse JSON | Lecture seule, délai borné, aucun effet métier |

**Transport unique obligatoire pour tous les modules applicatifs, existants et nouveaux : OTLP HTTP/protobuf pour les logs et les traces.** Les fichiers partagés, la collecte stdout/Docker et OTLP/gRPC ne sont pas des variantes conformes de ce contrat. La console et les fichiers locaux peuvent rester des copies de dépannage ; DiddiObserve ne doit pas les collecter en parallèle.

Le chemin /v1/logs ou /v1/traces est ajouté exactement une fois selon le SDK. Les endpoints spécifiques sont des URL complètes. Le comportement du SDK utilisé doit être testé.

La migration d'une intégration historique est décrite en section 4.3. Son maintien temporaire évite une interruption ; il ne constitue ni une exception permanente ni une conformité v2. Aucun réseau Docker partagé, volume partagé ou socket Docker n'est requis des applications.

### 2.1. Configuration universelle du raccordement

Cette section est la source normative unique pour toutes les équipes. Les fiches des modules contiennent uniquement leurs paramètres, références de secrets, correspondances de variables existantes et résultats de vérification ; elles ne définissent pas un autre protocole.

**Entrées disponibles en staging :**

| Entrée | Base publique | Usage |
| --- | --- | --- |
| HTTPS | `https://logs-otel.diddifree.com` | Disponible avec certificat reconnu par le magasin standard de l'image |
| HTTP MVP | `http://169.58.70.37:19480` | Reste accepté pour les intégrations actuelles ; trafic et identifiants non chiffrés |

Aucun raccordement ne DOIT être bloqué en attendant un réseau Docker commun ou une CA privée. La liaison du proxy HTTPS vers la passerelle centrale utilise actuellement l'IP publique. Les réseaux internes de stockage et le réseau utilisé pour le scrape sont des détails de la plateforme, pas une condition imposée à l'exporteur applicatif. Un changement HTTP vers HTTPS est explicite, sans rotation automatique des secrets.

Pour un service canonique `<service>`, les routes sont :

- Base OTLP : `<base>/otlp/<service>`.
- Traces : POST `<base>/otlp/<service>/v1/traces`.
- Logs : POST `<base>/otlp/<service>/v1/logs`.

L'exporteur utilise OTLP HTTP/protobuf. Le test de route avec une enveloppe JSON vide vérifie l'accès, pas la conformité de l'export réel. Un GET navigateur sur la racine ou sur la base peut répondre 404 ; un GET sur une route POST peut répondre 403. Ce ne sont pas des pages web.

### 2.2. Variables communes et compatibilité

Les nouveaux modules DOIVENT prendre en charge les variables suivantes dans leur configuration applicative **et dans le Compose utilisé par Portainer**. Les modules existants peuvent conserver leurs noms compatibles à condition de déclarer la correspondance dans leur fiche.

| Variable | Règle commune |
| --- | --- |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` obligatoire pour les logs et traces |
| `OTEL_SERVICE_NAME` | Nom canonique `<service>` ; le SDK reçoit `service.name` |
| `ENVIRONMENT` | Environnement de télémétrie, généralement `staging` pour ce MVP |
| `DEPLOYMENT_ID` | Identifiant du déploiement, distinct du nom du conteneur |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Base OTLP du service ; ajouter `/v1/traces` exactement une fois selon le SDK |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | URL complète facultative ; si fournie, prioritaire pour les traces, sans suffixe ajouté |
| `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` | URL complète des logs ; sans suffixe supplémentaire |
| `OTEL_EXPORTER_OTLP_HEADERS` | En-tête d'authentification dédié fourni par DiddiObserve, dans la syntaxe du SDK |
| `OTEL_LOGS_ENABLED` | Activation explicite de l'export des logs |
| `METRICS_BEARER_TOKEN` | Secret de scrape dédié, distinct des identifiants OTLP |

La version, l'instance, le composant et les autres attributs de la section 3 DOIVENT aussi être renseignés par le code ou des variables déclarées dans le manifeste. Une variable `APP_ENV` ayant des effets métier ne doit pas être remplacée aveuglément : sa correspondance avec l'environnement de télémétrie est explicite.

Une base OTLP vide désactive l'export de traces si aucune URL spécifique n'est fournie. `OTEL_LOGS_ENABLED=false` désactive les logs OTLP. Les modules possédant déjà un interrupteur global, tel que `OTEL_ENABLED`, déclarent aussi sa priorité. Aucun exporteur ne doit démarrer vers une adresse implicite localhost quand il est désactivé.

Les variables de CA ou de certificat client propres aux SDK restent vides pour ces entrées. HTTPS utilise le magasin standard de certificats, sans désactivation de vérification TLS. Une image dépourvue de racines publiques doit installer le paquet standard de confiance.

La configuration traverse obligatoirement les trois étapes : **Portainer → environment du Compose → settings/SDK du processus**. Créer les variables dans Portainer ne suffit pas. Tous les processus exporteurs (API, workers, tâches) doivent recevoir les paramètres nécessaires. Les contrôles affichent les URL et la présence des secrets, jamais leurs valeurs.

### 2.3. Travail commun à toutes les équipes

1. Brancher les événements structurés existants sur un exporteur de logs OTLP ; conserver la console si utile, sans double handler ni double export central.
2. Instrumenter les requêtes entrantes, les appels sortants et les tâches utiles ; propager le contexte W3C et corréler `trace_id`, `span_id` et `request_id`. Appliquer les formats et règles de cardinalité des sections suivantes.
3. Configurer des exports en arrière-plan, par lots, avec files et délais bornés, retries bornés et arrêt propre. Une panne de collecte ne bloque pas une opération métier et ne rend pas l'application non-ready.
4. Protéger le endpoint Prometheus déclaré par un token dédié : secret absent => 503 ; header absent/faux => 401 ou 403 ; bon Bearer => 200 au format Prometheus/OpenMetrics. Le chemin existant peut être conservé s'il est déclaré.
5. Relier les variables dans le Compose réellement déployé, puis redéployer. Fournir le SHA réellement exécuté, le contact et le manifeste. Les dépendances et hooks diffèrent selon le langage, pas les règles du protocole.

DiddiObserve fournit et active les routes, crée des secrets distincts pour chaque service/environnement, configure collecteurs et stockage, puis vérifie les données. Les équipes n'inventent ni URL ni secret. Le fichier privé de remise est hors Git ; un JSON public ne contient que les noms ou références des secrets. Un champ secret vide dans un modèle n'est jamais une instruction d'effacer un secret installé.

### 2.3.1. Raccordement réel des loggers et prévention des doublons

Cette règle s'applique à tous les langages et frameworks : l'existence d'un exporteur et d'une variable d'activation ne prouve pas que les événements applicatifs lui parviennent. Chaque équipe DOIT identifier le chemin réel entre le logger utilisé par son code, les éventuels parents, les handlers/appenders et l'exporteur. Les niveaux, filtres et configurations du serveur peuvent interrompre ce chemin.

Pour Python/Uvicorn notamment, un handler attaché uniquement au logger racine ne reçoit pas les événements d'une branche dont la propagation est désactivée. Le logger `uvicorn.error` peut transmettre à son parent `uvicorn`, qui arrête la propagation ; `uvicorn.access` peut aussi avoir son propre circuit. Ce piège concerne toute hiérarchie équivalente, pas seulement DiddiGo. Il faut vérifier la configuration effectivement chargée, pas supposer que tous les frameworks ont ce comportement.

L'équipe choisit et teste une seule stratégie par flux :

- raccorder le handler OTLP à la branche qui reçoit réellement les événements ;
- ou utiliser un logger applicatif dédié avec un chemin maîtrisé vers l'exporteur ;
- ou configurer explicitement la propagation vers la racine, en contrôlant les handlers déjà installés.

Ne pas activer globalement la propagation ni attacher le même exporteur à tous les parents sans vérifier les doublons. La présence d'une copie console est admise ; plusieurs exports centraux du même événement ne le sont pas. La configuration du serveur peut remplacer les handlers lors du démarrage : le raccordement DOIT rester effectif après l'initialisation réelle et être idempotent. Tester les processus API et workers séparément, ainsi que les modes multi-processus utilisés en déploiement.

Le handler DOIT accepter les messages JSON structurés et les messages texte ordinaires. Un échec de décodage JSON ne doit pas supprimer silencieusement un log texte ; appliquer le formatage et la protection des données prévus au protocole. Les erreurs d'export ne doivent pas réentrer dans le même handler et provoquer une boucle de journalisation.

**Test de raccordement obligatoire :** démarrer avec la configuration réelle du serveur, émettre un événement marqué via la fonction de journalisation réellement utilisée par l'application, puis vérifier qu'il atteint l'exporteur une seule fois. Tester aussi un message texte et les branches de logging incluses dans le périmètre, avec leurs niveaux et filtres. Un test appelant directement l'exporteur ne couvre pas ce risque. En environnement contrôlé, utiliser un exporteur mémoire ou factice ; après déploiement, retrouver le marqueur dans Loki avec la bonne identité et l'horodatage attendu. Vérifier la corrélation trace/span lorsqu'un contexte de trace est actif.

Les intégrations déjà validées conservent leur configuration si ce test passe. Les secrets et frameworks existants sont conservés ; les transports historiques doivent suivre la migration de la section 4.3.

### 2.4. Validation universelle avant déclaration de conformité

- L'application est saine et les paramètres sont présents dans les processus après déploiement.
- Les routes POST refusent un identifiant absent ou celui d'un autre module, puis acceptent celui du service. Cette vérification ne suffit pas à déclarer le producteur raccordé.
- Une requête non destructive et un événement repérable produisent de **vrais logs dans Loki et de vraies traces dans Tempo**, avec identité, environnement, horodatage récent et corrélation corrects.
- Les métriques sont contrôlées séparément : refus/succès du token, activation du scrape, cible UP et séries reçues. Des logs/traces présents ne prouvent pas que les métriques fonctionnent.
- Le test de raccordement de la section 2.3.1 passe avec la configuration réelle du serveur ; le marqueur est retrouvé une seule fois dans Loki.
- Une indisponibilité du collecteur ne fait pas échouer le métier ; absence de doublons et filtrage des secrets vérifiés.

Chaque signal a son propre état (`non configuré`, `route prête`, `producteur configuré`, `données reçues`, `validé`), daté et étayé. Une publication documentaire, un conteneur healthy ou une route qui répond 200 ne constituent pas à eux seuls une validation complète.

## 3. Identité et registre des services

Chaque processus applicatif DOIT publier les attributs suivants dans sa ressource OpenTelemetry et dans ses logs :

| Attribut | Valeur ou règle |
| --- | --- |
| `service.namespace` | `diddi` |
| `service.name` | Nom canonique du registre ; stable entre versions et répliques |
| `service.version` | Version de release ou SHA Git immuable ; jamais `latest` |
| `service.instance.id` | Identifiant unique du processus démarré ; renouvelé au redémarrage |
| `deployment.environment.name` | `development`, `test`, `staging` ou `production` |
| `diddi.deployment.id` | Identifiant stable de l’installation, distinguant deux déploiements d’un même service |
| `diddi.component` | `api`, `worker`, `scheduler`, `collector` ou `web` |
| `diddi.observability.version` | Version effectivement adoptée du contrat ; `2.0.0` après validation de cette révision |

Les attributs préfixés `diddi.` sont propres à ce contrat. L’environnement NE DOIT PAS être déduit du nom du serveur Portainer. La version de build DEVRAIT aussi figurer dans le label OCI `org.opencontainers.image.revision`.

Noms canoniques de départ :

| Service audité | `service.name` cible |
| --- | --- |
| DiddiFreeID / diddi-auth | `diddifree-id` |
| DiddiGo | `diddigo` |
| DiddiSend | `diddisend` |
| DiddiPay | `diddipay` |
| DiddiComms | `diddicomms` |
| DiddiFiles | `diddifiles` |
| DiddiFood | `diddifood` |
| DiddiSupport | `diddisupport` |
| DiddiMap / AbidjanMaps | `diddimap` |
| DiddiRecensement | `diddi-recensement` |
| DiddiFree Backoffice | `diddifree-backoffice` |
| DiddiFree Pilotage | `diddifree-pilotage` |
| DiddiFood Radar | `diddifood-radar` |
| DiddiReview Worker | `diddi-review-worker` |
| Plateforme d’observabilité | `diddi-observe` |

Un worker partage le nom de son service avec `diddi.component=worker`. L’ancien nom `diddicomms-worker` est un alias de migration. Le conteneur autonome `diddifree-radar` reste `unclassified` jusqu’à identification de son propriétaire et de son code ; il NE DOIT PAS être fusionné arbitrairement avec Pilotage ou Food Radar.

Chaque déploiement DOIT posséder un manifeste versionné contenant : propriétaire et contact opérationnel, dépôt, version, environnement, composants, adresse de collecte, chemins de santé/métriques, méthode d’authentification et références de secrets, dépendances critiques, politique de sampling, rétention, SLO, runbook, profil et état de conformité. Les secrets eux-mêmes NE DOIVENT PAS y figurer.

## 4. Contrat des logs

### 4.1 Structure obligatoire

Chaque événement applicatif DOIT comporter `schema_version`, `timestamp`, `level`, `event`, `message` et `resource` contenant les huit attributs d’identité. `schema_version` vaut `1.0.0`.

- `timestamp` : heure de l’événement en UTC, RFC3339 avec suffixe `Z`.
- `level` : `debug`, `info`, `warn`, `error` ou `fatal`, en minuscules.
- `event` : nom stable de catalogue, par exemple `http.request.completed`, `payment.provider.failed` ou `worker.cycle.completed`. Aucun identifiant dynamique dans son nom.
- `message` : texte court et nettoyé, compréhensible sans reconstruire le contexte.
- `attributes` : objet de champs supplémentaires documentés. Les clés et types restent stables.
- `request_id`, `trace_id`, `span_id` : présents lorsqu’un contexte réel existe. Les champs absents sont omis ; les chaînes vides, identifiants nuls et valeurs fictives sont interdits.

Exemple fictif d’une ligne, présenté indenté pour lecture :

```json
{
  "schema_version": "1.0.0",
  "timestamp": "2026-11-13T10:15:30.240Z",
  "level": "info",
  "event": "http.request.completed",
  "message": "Requête terminée",
  "resource": {
    "service.namespace": "diddi",
    "service.name": "diddisend",
    "service.version": "8254ea1656e037962e2fc0927ba2be3a663d55ea",
    "service.instance.id": "diddisend-api-example-01",
    "deployment.environment.name": "staging",
    "diddi.deployment.id": "diddisend-staging",
    "diddi.component": "api",
    "diddi.observability.version": "1.0.0"
  },
  "request_id": "req_1df3cc0d90ef47ba81dd75fd277b470c",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "attributes": {
    "http.request.method": "GET",
    "http.route": "/deliveries/{delivery_id}",
    "http.response.status_code": 200,
    "duration_ms": 240
  }
}
```

Pour HTTP, le log de fin DOIT contenir méthode, route normalisée, statut et durée monotone en millisecondes. Une exception avant réponse DOIT produire un événement d’échec et être comptée. Une réponse de streaming DOIT être mesurée jusqu’à sa fin ou son interruption, pas seulement jusqu’à l’envoi des en-têtes. Les WebSockets utilisent des événements connexion/déconnexion et des compteurs dédiés, sans contenu de messages.

Les exceptions utilisent `error.code`, `error.type`, `error.message` et, si nécessaire, `error.stack`, dans `attributes`. Les traces de pile sont encodées dans le JSON, sans lignes autonomes. Les adaptateurs OTel PEUVENT mapper ces champs vers les conventions natives d’exception.

La taille maximale d’une ligne est **64 KiB UTF-8**. Le producteur tronque d’abord message et pile, conserve l’identité et marque `attributes.truncated=true`. Un événement impossible à sérialiser ne doit pas faire échouer l’opération métier ; son rejet DOIT être compté.

### 4.2 Données autorisées et collecte

Sont interdits : mots de passe, PIN/OTP, tokens, cookies, clés API, en-têtes d’authentification, URLs signées, corps complets de requêtes/réponses et données de paiement sensibles, sous réserve de l'exception OTP strictement bornée ci-dessous. Téléphones, emails, coordonnées précises, adresses et IP complètes sont exclus par défaut. Tout besoin exceptionnel doit être documenté avec accès et rétention spécifiques ; aucune exception OTP ne vaut autorisation d'exposer d'autres secrets.

**Exception temporaire confirmée par l'utilisateur le 16 novembre 2026 :** DiddiFree ID en staging peut conserver les événements OTP en clair prévus par son dispositif de diagnostic, avec leur destinataire et l'interrupteur `OTP_LOG_PLAINTEXT`. Cette décision ne bloque pas le raccordement des métriques et traces et ne DOIT PAS être annulée implicitement par une configuration de collecte. Le responsable du module DOIT documenter les événements/champs concernés, les lecteurs autorisés, la rétention, la portée locale ou centrale, le responsable et l'échéance de réexamen, ainsi que la procédure de désactivation. La portée centrale n'est pas déduite de la seule activation locale. Aucun rattrapage de logs historiques n'est autorisé implicitement. Les tests utilisent des valeurs synthétiques ; les écarts C03 restent déclarés, sans certification automatique. Cette exception ne s'étend ni aux autres modules ni à la production.

Les identifiants métier nécessaires au diagnostic peuvent être présents dans `attributes` selon une liste autorisée. Ils ne sont jamais des labels de métriques ou d’index Loki. La pseudonymisation utilise un mécanisme contrôlé ; un simple hash d’un téléphone ne garantit pas sa confidentialité.

Les logs d’accès du serveur, les messages de librairies et les logs métier DOIVENT passer par le même dispositif de nettoyage. La collecte Docker ne rend pas un message applicatif automatiquement conforme. Le collecteur enrichit l’identité à partir d’une source de confiance, contrôle les divergences et ne permet pas à un service d’usurper l’identité d’un autre.

Les logs de santé et de scrape réussis PEUVENT être filtrés pour réduire le bruit. Le filtrage et tout échantillonnage des logs sont déclarés ; les erreurs ne sont pas supprimées silencieusement.

### 4.3 Migration des transports historiques vers OTLP

La cible est identique pour chaque API, worker et tâche : logger applicatif → exporteur OTLP HTTP/protobuf → passerelle DiddiObserve → Alloy → Loki. Le schéma JSON des événements reste 1.0.0 ; cette migration porte sur leur transport, pas sur les règles métier.

1. L'équipe du module raccorde son logger existant à un exporteur OTLP et transmet les variables à chaque processus. Elle conserve le même service.name et distingue diddi.component=api, worker ou scheduler.
2. DiddiObserve fournit les endpoints et les secrets dédiés, puis vérifie les attributs, la réception et la corrélation. Une implémentation locale seule ne suffit pas.
3. Avant la bascule générale, valider un marqueur OTLP synthétique exclu du flux fichier, ou un processus canari non collecté par fichiers. Ne pas exporter simultanément les événements métier par les deux chemins.
4. Coordonner la désactivation de la collecte historique et l'activation OTLP générale. Prévoir un retour arrière borné ; aucun rattrapage automatique des archives. Documenter la fenêtre de bascule et toute perte ou duplication éventuelle.
5. Vérifier séparément API et workers dans Loki, puis retirer le montage partagé du collecteur central. Les fichiers et volumes du producteur ne sont pas supprimés par DiddiObserve.

Tant que la bascule n'est pas vérifiée, le manifeste déclare target_transport=otlp-http/protobuf, le transport réellement utilisé, un responsable, une échéance et migration_required=true. Il ne déclare pas la conformité v2.

DiddiFreeID est actuellement dans cet état transitoire : lecture des deux fichiers actifs côté central, traces OTLP et métriques déjà raccordées. Cette description est un état de migration, jamais une alternative offerte aux autres équipes.


## 5. Corrélation et traces distribuées

### 5.1 Requêtes HTTP

Les services DOIVENT extraire et injecter le contexte W3C `traceparent` et `tracestate` avec un propagateur standard. Un contexte invalide est ignoré et une nouvelle trace est créée. Ces en-têtes ne constituent jamais une preuve d’identité ou d’autorisation.

Chaque opération entrante possède un span serveur ; chaque appel sortant instrumenté possède son span client. Les accès DB/cache et les opérations métier significatives DEVRAIENT être instrumentés. Une opération ne doit pas créer de spans en double à cause d’une instrumentation manuelle et automatique superposée.

`X-Request-ID` est accepté s’il correspond à `[A-Za-z0-9._-]{1,128}`, sinon remplacé par un identifiant généré. Il est renvoyé au client et propagé dans la chaîne synchrone. Il reste distinct de `trace_id`, qui comprend 32 caractères hexadécimaux minuscules non tous nuls ; `span_id` en comprend 16. Les valeurs sont extraites du contexte actif, jamais construites à partir d’un identifiant métier.

Pendant la migration, `X-Correlation-ID` peut être accepté comme alias si `X-Request-ID` est absent et si sa valeur est valide. En cas de conflit, `X-Request-ID` prévaut ; aucun en-tête non validé n’est recopié dans les logs. Le contexte local DOIT être réinitialisé à la fin de chaque requête ou job.

### 5.2 Messages, outbox et reprises

Le producteur DOIT transmettre le contexte dans les métadonnées techniques du message : `traceparent`, `tracestate` si présent, `request_id` si présent, identifiant du message, corrélation métier et numéro de tentative lorsqu’ils existent. L’ajout respecte le contrat d’événement existant et doit être coordonné avec ses consommateurs.

Le consommateur DOIT ouvrir un nouveau span de traitement, extraire le contexte, puis le nettoyer après traitement. Une nouvelle tentative garde l’identité métier du message mais crée un nouveau span. Pour un traitement différé ou un lot à plusieurs origines, utiliser des liens de spans vers les contextes d’origine au lieu de prétendre à un parent unique. La politique parent/lien DOIT être documentée par canal.

Une tâche planifiée crée sa propre trace et un identifiant d’exécution. Un `map_trace_id` de trajet reste un attribut métier ; il ne remplace jamais un identifiant OpenTelemetry.

### 5.3 Export et échantillonnage

L’export est asynchrone, par lots et avec files bornées. Le sampler respecte le parent sur les échanges internes de confiance. Valeurs initiales : 100 % des traces du scénario de validation, 10 % des nouvelles traces de production, taux configurable par service. À la frontière publique, la décision de sampling est contrôlée par l’infrastructure : un client ne doit pas pouvoir forcer une collecte illimitée.

Le sampling en début de trace ne garantit pas la conservation de toutes les erreurs. Une promesse de conservation de toutes les traces en erreur exige un dispositif adapté, avec une collecte en amont et une capacité validées. Les métriques et logs d’erreur restent disponibles indépendamment du sampling des traces.

## 6. Contrat des métriques

### 6.1 Exposition et familles communes

Les nouveaux services DEVRAIENT utiliser `/internal/metrics`. Les chemins actuels, dont `/metrics`, restent admis s’ils sont déclarés dans le manifeste et protégés. Un chemin unique n’est pas une condition de conformité.

La famille canonique DIDDI est définie ci-dessous. Les unités de base sont les secondes et les octets. Les implémentations OTel peuvent utiliser leurs instruments natifs à condition que l’adaptateur fournisse la vue canonique sans double comptage.

| Métrique canonique | Type | Labels applicatifs autorisés |
| --- | --- | --- |
| `diddi_http_server_requests_total` | Compteur | `method`, `route`, `status_code` |
| `diddi_http_server_request_duration_seconds` | Histogramme | `method`, `route` |
| `diddi_dependency_requests_total` | Compteur | `dependency`, `operation`, `outcome` |
| `diddi_dependency_request_duration_seconds` | Histogramme | `dependency`, `operation` |
| `diddi_jobs_total` | Compteur | `job_type`, `outcome` |
| `diddi_job_duration_seconds` | Histogramme | `job_type` |
| `diddi_worker_heartbeat_timestamp_seconds` | Jauge | `worker_type` |
| `diddi_queue_pending` | Jauge | `queue` |
| `diddi_queue_oldest_age_seconds` | Jauge | `queue` |
| `diddi_queue_dead_letter` | Jauge | `queue` |
| `diddi_telemetry_dropped_total` | Compteur | `signal`, `reason` |

HTTP est obligatoire pour les API ; jobs/heartbeat pour les workers et tâches ; queues pour les composants qui les gèrent. Les familles non applicables sont déclarées comme telles. Pour les tâches planifiées, le manifeste précise cadence, délai maximal et échéance suivante ; l’alerte de fraîcheur ne suppose pas une boucle permanente.

Les labels de cible `service_name`, `environment`, `deployment_id`, `component` et `instance` sont ajoutés par la collecte depuis le registre. `instance` désigne la cible technique, pas un utilisateur. La version est portée par une métrique d’information, pas par chaque série.

### 6.2 Cardinalité, durées et précision

`route` DOIT être le template du routeur, par exemple `/orders/{order_id}`. Les routes inconnues utilisent `/_unmatched` ; la normalisation ne se limite pas aux UUID. Méthodes non reconnues : `OTHER`. Les valeurs de `dependency`, `operation`, `outcome`, `job_type`, `queue` et `reason` proviennent de catalogues bornés.

User ID, request ID, trace ID, message ID, téléphone, email, IP, URL brute, query string et messages d’erreur libres sont interdits comme labels. Les labels ne servent pas à transporter le contexte complet d’une opération.

Les histogrammes classiques constituent la base portable v1. Bornes HTTP initiales en secondes : `0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, +Inf`. Les buckets de jobs sont adaptés à leur durée et documentés. Un histogramme natif peut être adopté si toute la chaîne est compatible et testée. Des séries de buckets incompatibles ne doivent pas être agrégées dans un même calcul de quantile.

Les compteurs ne diminuent qu’au redémarrage. Les durées utilisent une horloge monotone. Les nombres monétaires ne sont pas des compteurs financiers de référence. Les métriques métier supplémentaires sont définies dans une annexe propre au service.

Une instance multi-processus DOIT agréger correctement ses métriques ou exposer chaque processus séparément. Un scrape servi aléatoirement par plusieurs registres mémoire indépendants est non conforme.

Budget initial : au plus **20 000 séries actives par cible applicative**, toutes familles comprises. Le budget peut être ajusté par le responsable de la plateforme après mesure. Le dépassement déclenche une alerte et une analyse des labels ; les suppressions éventuelles restent explicites et comptabilisées.

## 7. Santé et disponibilité

La liveness indique que le processus répond ; elle NE DOIT PAS dépendre d’un service aval. La readiness indique qu’il peut accomplir son rôle essentiel et DOIT vérifier réellement ses dépendances critiques, pas seulement la présence d’une variable.

| État de readiness | HTTP | Signification |
| --- | --- | --- |
| `ready` | 200 | Capacités essentielles disponibles |
| `degraded` | 200 | Capacité essentielle disponible, dépendance facultative défaillante ; état explicitement visible |
| `unavailable` | 503 | Dépendance critique indisponible ou initialisation non terminée |

Les dépendances critiques et facultatives sont déclarées dans le manifeste. Une dépendance métier non critique ne doit pas déclencher une cascade de retrait de trafic. Une panne de DiddiObserve n’est jamais une cause de non-readiness d’un service métier.

Les sondes ont un délai total initial de **3 secondes**, avec délai individuel plus court et contrôle de concurrence. Elles ne déclenchent ni paiement, ni envoi de message, ni modification de données. Une vérification réussie antérieure ne peut pas être présentée comme fraîche au-delà du TTL déclaré.

Réponse privée de référence :

```json
{
  "status": "degraded",
  "service": "diddisend",
  "checked_at": "2026-11-13T10:15:30.240Z",
  "checks": {
    "database": {"status": "up", "critical": true},
    "payment_provider": {"status": "down", "critical": false}
  }
}
```

Les réponses publiques restent minimales, sans adresses internes ni exceptions. Les détails sont disponibles seulement sur le réseau ou l’interface d’exploitation autorisés.

Un worker longue durée DOIT produire un heartbeat après une boucle correctement exécutée, même sans travail. Une boucle bloquée ne rafraîchit pas le heartbeat. Les jobs ponctuels DOIVENT exposer résultat, début, fin et durée via un mécanisme de collecte durable adapté ; une absence de processus après succès n’est pas une panne.

## 8. Sécurité et isolation

Les métriques et endpoints d’ingestion DOIVENT être authentifiés. L’ingestion publique est autorisée selon la section 2.1 : HTTPS disponible et exception HTTP publique explicitement acceptée pour le MVP staging. Hors de cette exception, les transports distants utilisent TLS avec certificats vérifiés. Les endpoints de scrape restent limités au collecteur autorisé. Un service ancien sans authentification native peut passer par une passerelle privée authentifiée, à condition que son accès direct soit effectivement bloqué.

Sans authentification valide, la collecte est refusée. Sans configuration de secret, l’endpoint reste fermé ; il ne doit pas devenir public par défaut. Les identifiants de scrape sont propres à chaque service/environnement, révocables et renouvelables. Aucun token utilisateur ou clé d’administration Portainer ne sert de secret de collecte.

DiddiObserve fournit les routes et secrets selon la section 2.1 à 2.3. L'authentification OTLP et le token de scrape sont distincts. Les logs et traces applicatifs utilisent les identifiants OTLP dédiés ; aucun volume partagé n'est requis. Les clés privées TLS restent côté plateforme. Aucun secret métier n'est réutilisé.

La lecture des logs Docker utilise une capacité limitée aux opérations nécessaires. Un montage de `docker.sock` en lecture seule ne limite pas les méthodes de l’API Docker. Une autorisation d’audit ponctuel via Portainer ne vaut pas autorisation permanente pour un collecteur.

L’interface d’exploitation DOIT distinguer lecteur, opérateur et administrateur ; séparer production et staging ; journaliser les changements de configuration et d’accès. Si le backend ne sait pas isoler les données par service, l’architecture doit assurer cette séparation ; masquer un dashboard ne constitue pas un contrôle d’accès.

## 9. Collecte, stockage et résilience

Paramètres initiaux du profil standard, à inscrire dans le manifeste :

| Paramètre | Valeur initiale |
| --- | --- |
| Scrape métriques | Toutes les 15 s ; timeout 5 s |
| Sonde de disponibilité | Toutes les 30 s ; timeout total 3 s |
| Flush des traces | Au plus 5 s entre lots, hors saturation |
| Timeout d’un export | 5 s ; export hors chemin métier |
| File de spans du producteur | 2 048 spans ; limite mémoire documentée |
| Arrêt gracieux du producteur | Flush borné à 5 s |
| Logs techniques centraux | 14 jours en staging, 30 jours en production |
| Traces | 7 jours en staging, 14 jours en production |
| Métriques | 30 jours en staging, 90 jours en production |
| Copies locales facultatives | Budget borné déclaré ; jamais un transport central alternatif |
| Rotation Docker cible si stdout conservé | 10 MiB par fichier, 5 fichiers par conteneur, ou budget équivalent documenté ; indépendante de la rotation applicative |

Les rétentions sont des durées maximales du profil technique ; elles ne définissent pas la rétention réglementaire ou métier des journaux d’audit. Les copies, sauvegardes et exports doivent suivre une politique d’expiration cohérente. Le stockage nécessaire DOIT être calculé à partir des débits mesurés, avec marge et alerte de capacité avant activation générale.

Les exporteurs DOIVENT utiliser reprises bornées avec backoff et jitter, respecter les réponses de limitation et compter pertes, rejets et échecs. Une reprise infinie ne doit pas remplir la mémoire ou le disque. Les files et positions du collecteur DEVRAIENT être persistantes, avec quotas et comportement documenté en cas de disque plein.

L’observabilité fournit une livraison au mieux avec reprises ; elle ne promet pas une livraison exactement une fois. Des doublons et pertes peuvent survenir. Les tableaux de bord techniques ne doivent pas utiliser les logs comme registre comptable.

La plateforme DOIT superviser sa propre ingestion : dernière donnée reçue, backlog d’export, taux de rejet, pertes, disque et erreurs d’authentification. Une absence de données doit apparaître comme `unknown` ou `no data`, jamais comme zéro erreur ou disponibilité parfaite.

## 10. Tableaux de bord et alertes

Trois niveaux sont obligatoires : vue plateforme, vue service/composant, investigation par opération. Les filtres communs sont service, environnement, déploiement, composant et intervalle de temps. Les liens logs → trace et trace → logs reposent sur le véritable `trace_id`. Une trace non retenue par sampling est signalée comme indisponible.

La vue plateforme affiche : couverture de collecte, état des sondes, volume de requêtes, taux de 5xx, latence lorsqu’elle est calculable, état des workers et pertes de télémétrie. Les erreurs métier et les réponses 4xx sont présentées séparément des erreurs serveur. Les métriques métier détaillées restent rattachées à leur service.

Chaque alerte DOIT comporter propriétaire, service, environnement, sévérité, description de l’impact et lien vers un runbook. Regroupement et déduplication évitent les notifications par réplique. Une seule chaîne de routage est propriétaire de chaque famille d’alertes ; un test de notification doit être explicitement autorisé.

Règles techniques de départ : cible non scrappable pendant 2 min ; readiness indisponible pendant 2 min ; heartbeat de worker continu âgé de plus de trois périodes et au moins 60 s ; données attendues absentes ; perte persistante de télémétrie ; capacité disque selon le budget du stockage. Le backlog et les tâches planifiées utilisent leurs seuils déclarés, pas une valeur universelle.

Les alertes de taux d’erreur et de latence DOIVENT s’appuyer sur le SLO du service et un volume minimum pertinent. Un SLO n’est pas déduit de l’existence d’un dashboard. Jusqu’à sa définition, l’interface indique `SLO non défini`.

## 11. Compatibilité et migration

La migration comporte trois états :

| État | Signification |
| --- | --- |
| `inventoried` | Identité, propriétaire et capacités recensés |
| `connected` | Ingestion réellement démontrée pour les signaux déclarés, avec lacunes explicites |
| `conformant-v1` | Tous les critères applicables validés sur la version déployée |

La normalisation des anciens logs se fait dans un adaptateur par source : `ts` ou `at` → `timestamp`, casse du niveau → niveau canonique, `service`/`app` → identité vérifiée. `release` ne devient `service.version` que si sa valeur désigne effectivement la version. Une heure d’ingestion ne doit pas être présentée comme l’heure réelle de l’événement : en l’absence de timestamp source, conserver cette distinction et marquer le format legacy.

Une route `/metrics` peut rester inchangée. Les noms de métriques existants peuvent être normalisés par règles de collecte/enregistrement lorsque leur sémantique le permet. Les sommes en ms peuvent être converties en secondes ; les buckets manquants et p95 ne peuvent pas être inventés. Le registre indique quelle source alimente chaque série canonique afin d’éviter le double comptage.

Chaque exception de migration DOIT comporter propriétaire, motif, périmètre, mesure compensatoire et échéance. Par défaut, réexamen sous 30 jours. Un service avec exception bloquante reste `connected`, pas `conformant-v1`.

### Priorités par service issues de l’audit

| Service | Travaux attendus du responsable |
| --- | --- |
| DiddiSend | Résoudre le 503 de collecte, déclarer identité/version, normaliser les logs et vérifier l’export OTLP réel |
| DiddiPay | Réutiliser instrumentation et heartbeat ; aligner schéma/identité ; prouver la corrélation API, outbox et worker |
| DiddiComms | Compléter identité/environnement ; santé API/worker ; vérifier propagation asynchrone et collecte des métriques |
| DiddiFreeID | Fermer les métriques publiques ; ajouter traces ; préparer la migration de sa collecte sans doublons |
| DiddiGo | Fermer les métriques publiques ; ajouter histogrammes et traces ; borner toutes les routes de métriques |
| DiddiFood | Fermer les métriques publiques ; JSON sans préfixe ; histogrammes et traces ; diagnostiquer les docs unhealthy séparément |
| DiddiFiles | Fermer les métriques par défaut ; UTC explicite ; identité, traces et healthcheck Docker API |
| DiddiSupport | Readiness avec connectivité réelle ; JSON conservant les champs supplémentaires ; métriques HTTP ; protéger et surveiller l’outbox |
| DiddiMap | Logs JSON ; métriques et traces ; santé réelle du moteur/DB et codes HTTP cohérents |
| DiddiRecensement | Socle Express complet : corrélation, logs structurés, métriques, traces et readiness DB |
| Backoffice | Instrumenter API/worker ; préserver le journal métier/audit ; centraliser les logs techniques |
| Pilotage | Ajouter identité, timestamp et niveau systématiques ; métriques techniques et fraîcheur du collecteur |
| Food Radar | Même socle que Pilotage, avec identité distincte et vérification de sa propre révision |
| Review Worker | Alias de corrélation ; readiness réelle ; métriques de jobs, logs JSON et traces |
| Radar autonome | Identifier dépôt, propriétaire et rôle avant classification |

Les constats correspondent à l’audit daté et DOIVENT être revérifiés avant intervention. L’adoption du protocole n’autorise aucune intervention hors périmètre.

## 12. Critères de conformité

La validation s’effectue sur un environnement isolé ou sur un scénario explicitement autorisé, avec données synthétiques et sans déclencher de transaction réelle non prévue.

| ID | Preuve obligatoire |
| --- | --- |
| C01 | Manifeste complet, version déployée identifiable et identité cohérente entre logs, métriques et traces |
| C02 | Logs JSON valides pour succès, exception, librairies et démarrage ; schéma, UTC, limites de taille et nettoyage vérifiés |
| C03 | Secrets synthétiques injectés dans les cas d’erreur absents des logs et traces ; aucune donnée interdite dans les labels ; exception OTP éventuelle explicitement rapportée avec sa portée et son interrupteur, sans prétendre à une réussite sans réserve |
| C04 | Succès, 4xx et 5xx comptés correctement ; histogramme réel ; route stable face à au moins 100 identifiants et 100 URLs inconnues |
| C05 | Collecte sans identifiant ou avec identifiant invalide refusée ; configuration manquante fermée ; accès direct non protégé impossible |
| C06 | Requête synthétique traversant deux services : parenté vérifiée, logs corrélés ; contexte malformé traité sans échec ; pas de fuite entre requêtes |
| C07 | Pour l’asynchrone : publication, consommation et reprise reliées ; spans distincts par tentative ; aucune double exécution métier induite par la télémétrie |
| C08 | Liveness reste positive lors d’une panne aval ; readiness passe à 503 pour une dépendance critique ; dégradation facultative explicitement signalée |
| C09 | Heartbeat/fraîcheur, backlog et durée des jobs visibles selon le profil ; boucle bloquée détectée |
| C10 | Collecteur indisponible pendant 5 min : opérations métier possibles, ressources bornées, pertes/reprises mesurées, récupération démontrée |
| C11 | Preuve d’arrivée au stockage et de consultation Grafana, corrélation logs/traces, affichage correct de l’absence de données |
| C12 | Rétention/rotation configurées, sauvegardes couvertes, règles d’alertes vérifiées et runbooks attribués ; pour OTLP : export par lots, files bornées, arrêt propre, panne du collecteur et absence de doublons vérifiés |

Une simple présence de SDK, un conteneur `running` ou un endpoint `200` ne suffit pas. Le rapport de conformité contient résultats, horodatage, environnement, révision, preuves et exceptions. Les critères non applicables doivent être justifiés. Aucun des services audités n’est certifié par le présent document.

## 13. Versionnement et adoption

La version suit `MAJOR.MINOR.PATCH` : changement incompatible de type, unité ou sémantique → majeur ; ajout compatible → mineur ; correction rédactionnelle → patch. Les consommateurs v1 DOIVENT ignorer les champs supplémentaires inconnus. Une propriété ne doit pas changer silencieusement de sens.

**Révision 1.1.3 :** raccordement MVP par HTTP public par IP sans attendre HTTPS, sans CA à distribuer aux modules. Aucun changement de schéma JSON, de token ou de nom de métrique ; aucune migration obligatoire des transports déjà validés. Voir [les instructions de migration des équipes](docs/teams/MIGRATION-V1.md).

**Révision 1.1.0 :** ajout du profil commun de fichiers JSON rotatifs et des responsabilités de montage/collecte, précision des secrets/TLS dans les guides et formalisation de l'exception temporaire OTP. Le schéma des événements reste `schema_version=1.0.0` ; les noms et unités des métriques ne changent pas. Les producteurs déjà raccordés par OTLP ou une collecte stdout validée peuvent conserver leur transport. Ils ne déclarent `diddi.observability.version=1.1.0` qu'après adoption vérifiée des obligations applicables. Les exemples d'événements 1.0.0 restent lisibles ; publier ce document ne change pas leurs versions déployées.

L’ordre d’adoption est : registre et accès de collecte ; pilote sur les services déjà instrumentés ; validation du parcours distribué ; extension aux autres API ; workers et tâches ; suppression contrôlée des anciens collecteurs après vérification de couverture. Chaque bascule prévoit un retour arrière de configuration et interdit la double ingestion durable.

Les responsables de services implémentent les adaptations dans leurs propres dépôts. DiddiObserve reste propriétaire de la normalisation transitoire et des vues communes. Toute modification de politique — sampling, rétention, seuils ou budgets — est versionnée, datée et attribuée.

## Références

- [Audit DIDDI du 13 novembre 2026](docs/AUDIT.md) et [inventaire technique](registry/services.json).
- [Ressources OpenTelemetry](https://opentelemetry.io/docs/concepts/resources/) et [attribut d’environnement](https://opentelemetry.io/docs/specs/semconv/resource/deployment-environment/) : identité et environnement des producteurs.
- [Propagation de contexte OpenTelemetry](https://opentelemetry.io/docs/concepts/context-propagation/) : corrélation distribuée.
- [Spécification OTLP](https://opentelemetry.io/docs/specs/otlp/) : protocole d’export.
- [Nommage Prometheus](https://prometheus.io/docs/practices/naming/) et [histogrammes](https://prometheus.io/docs/practices/histograms/) : unités, séries et distributions.
- [Cardinalité Loki](https://grafana.com/docs/loki/latest/get-started/labels/cardinality/) : choix des labels d’index.

## Remise opérationnelle et versionnement

**Révision 1.2.0 :** règles universelles de raccordement réunies en section 2 ; HTTP public MVP et HTTPS public explicités ; suppression du réseau partagé et de la CA privée comme prérequis d'export ; OTLP logs/traces comme profil commun des nouveaux modules. Les profils fichier existants restent compatibles. Le schéma des événements reste **1.0.0** ; aucune rotation de secrets ni modification automatique des modules.

[Point d'entrée des équipes](docs/TEAM-HANDOFF.md). Les fiches de chaque module consignent les paramètres et diagnostics ; elles ne remplacent aucune règle de ce protocole.

**Révision 2.0.0 — 18 novembre 2026 :** clarification du raccordement des loggers, de la propagation, des niveaux/filtres, de l’initialisation et de la prévention des doublons. Ajout du test passant par le logger applicatif réel. Aucun changement du schéma des événements (1.0.0), des routes ou des secrets.

## Révision 2.0.0 — uniformisation obligatoire

Cette révision remplace les autorisations de transports alternatifs des révisions 1.x historiques ci-dessus. Une fiche module, un exemple ancien ou un manifeste ne peut pas réintroduire une variante. Toute évolution du transport exige une révision du protocole commun avant adoption, et non un guide propre à un service.

Le protocole de transport reste commun ; seules l'identité, les adresses fournies, les références de secrets et les correspondances de variables historiques diffèrent. Les chemins métriques existants restent déclarés, sans changement métier imposé. Les composants tiers/infrastructure et web-edge gardent leur profil distinct ; ils ne constituent pas une exception pour une API ou un worker DIDDI.

La conformité 2.0.0 exige des preuves datées pour logs, traces et métriques de chaque composant applicable. Les JSON de remise distinguent la cible de l'état réellement observé. Aucune version déployée n'est relevée automatiquement.

La rétention reste centralisée : 14 jours pour les logs staging actuellement configurés. Une conservation sans expiration ou un archivage long terme reste une décision à valider et dimensionner ; cette révision ne l'active pas. Aucun module ne choisit sa propre durée de conservation centrale.

L'exception OTP staging existante reste explicite et temporaire : otp.code et otp.recipient sont acceptés dans le corps des logs DiddiFreeID, jamais comme labels. Elle ne change pas le transport, n'autorise aucun autre secret et ne s'étend pas à la production. La bascule OTLP doit vérifier ce traitement avec des valeurs synthétiques avant activation générale.
