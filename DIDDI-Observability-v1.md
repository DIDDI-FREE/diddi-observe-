# DIDDI Observability v1

**Version : 1.1.0 — 16 novembre 2026**
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
  ├─ logs JSON → fichier rotatif partagé (lecture seule) → Alloy → Loki
  │             ou transport OTLP logs déclaré et validé
  ├─ endpoint métriques privé ← Prometheus
  └─ traces OTLP → collecteur → stockage de traces
                                      ↓
                  Grafana : plateforme, service, opération
```

La référence cible utilise Grafana, Prometheus, Loki et un collecteur compatible OpenTelemetry. Alloy est une option cohérente avec l’existant. Le stockage de traces peut être Tempo ou Jaeger : les producteurs DOIVENT utiliser OTLP afin de rester indépendants de ce choix.

Les services NE DOIVENT PAS appeler les API métier d’autres services pour alimenter les tableaux de bord techniques. Des sondes de santé bornées et des métriques sur les appels métier réellement exécutés sont autorisées.

| Signal | Transport de référence | Règle |
| --- | --- | --- |
| Logs applicatifs | JSON UTF-8 par ligne dans un fichier rotatif partagé ; OTLP logs admis | Une seule chaîne centrale par événement ; stdout seul n'active aucune collecte |
| Métriques | Scrape HTTP(S), exposition Prometheus/OpenMetrics | Cible privée et authentifiée, découverte par manifeste |
| Traces | OTLP HTTP/protobuf | Adresse du collecteur configurable ; TLS et authentification hors transport local explicitement isolé |
| Santé | GET HTTP(S), réponse JSON | Lecture seule, délai borné, aucun effet métier |

OTLP/gRPC peut être utilisé si le manifeste le déclare. Pour HTTP, l’endpoint générique et l’endpoint spécifique aux traces DOIVENT être distingués : le chemin `/v1/traces` ne doit être ni oublié ni ajouté deux fois. Le comportement exact du SDK et de sa version DOIT être testé.

Le fichier partagé est le profil standard des nouveaux raccordements sur un même hôte Docker. Un transport OTLP logs déjà validé peut être conservé sans migration forcée. Une collecte stdout existante reste admise si son collecteur est explicitement déclaré et autorisé ; la stack centrale actuelle ne collecte pas automatiquement stdout. Sur des hôtes différents, un volume Docker local ne suffit pas : utiliser OTLP ou un collecteur local autorisé. Les paramètres opérationnels actuellement fournis sont documentés dans [le guide central](docs/ONBOARDING-READY.md).

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
| `diddi.observability.version` | Version effectivement adoptée du contrat ; `1.1.0` après validation de cette révision |

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

### 4.3 Convention universelle de fichiers et volumes

Le contrat, les variables et le schéma sont communs ; le branchement au logger dépend du langage. L'adaptation DOIT rester dans le dispositif de journalisation et la configuration de déploiement : les routes, règles et transactions métier ne doivent pas être réécrites pour ouvrir des fichiers de logs.

| Paramètre | Convention |
| --- | --- |
| `OBSERVABILITY_LOG_FILE` | Chemin absolu lu par le logger ; défaut de référence `/var/log/diddifree/observability.jsonl` |
| `OBSERVABILITY_LOG_VOLUME_NAME` | Variable Compose ; `<service.name>-observability-logs-<environment>` pour un déploiement unique |
| Plusieurs déploiements dans le même environnement | Ajouter un suffixe de déploiement stable au nom du volume ; aucune fusion implicite |
| Répertoire du producteur | `/var/log/diddifree`, volume monté en lecture/écriture |
| Répertoire du collecteur | `/var/log/inputs/<registry-id>`, même volume externe monté en lecture seule |
| Format | UTF-8, un objet JSON complet par ligne terminée par un saut de ligne ; schéma de la section 4.1 |
| Rotation initiale | Seuil de 10 MiB par fichier actif, 5 archives maximum par écrivain ; environ 60 MiB plus marge par écrivain |

`OBSERVABILITY_LOG_VOLUME_NAME` n'est pas un mécanisme de création de fichier applicatif. Le Compose DOIT l'utiliser pour nommer le volume et transmettre `OBSERVABILITY_LOG_FILE` au processus. Le logger DOIT lire le chemin, créer/ouvrir le fichier et gérer la rotation. Les variables seules dans Portainer n'implémentent aucun de ces comportements. Les réglages de rotation propres à chaque bibliothèque sont déclarés dans le manifeste ; aucun nom de variable supplémentaire n'est supposé reconnu universellement.

Un volume est dédié au service, à l'environnement et au déploiement. Le producteur crée le volume nommé ; Alloy le référence comme `external: true` après vérification de son existence sur le même hôte. Aucun socket Docker ni montage de `/var/lib/docker` n'est nécessaire. Le montage porte sur le répertoire complet afin que la rotation reste possible.

Le processus applicatif DOIT pouvoir écrire et Alloy lire les fichiers : définir les UID/GID et permissions de répertoire/fichier compatibles au déploiement, sans recourir à `chmod 777` ni exécuter l'application en root uniquement pour les logs. Le collecteur NE DOIT PAS modifier, supprimer ou faire tourner les fichiers du producteur.

### 4.4 Rotation, concurrence et continuité

- Un seul écrivain/gestionnaire de rotation est autorisé par fichier. Plusieurs workers ou répliques DOIVENT utiliser un gestionnaire central de journalisation compatible avec leur concurrence, ou des fichiers distincts, par exemple `observability-api-<instance>.jsonl` et `observability-worker-<instance>.jsonl`. Un simple handler de rotation par processus sur un fichier commun n'est pas une preuve de sûreté.
- Préférer renommage du fichier actif puis réouverture. Toute stratégie de type `copytruncate` nécessite une preuve explicite des pertes/doublons acceptés. Tester la poursuite de lecture avant et après rotation et redémarrage.
- Alloy DOIT suivre la liste exacte des fichiers actifs déclarés (ou un motif borné pour les instances). Ne pas inclure les archives et les fichiers compressés par un glob général : leur relecture peut dupliquer les événements. Déclarer le comportement au premier démarrage et en reprise ; les positions du collecteur sont persistées dans son propre volume, pas dans le volume producteur monté en lecture seule.
- Le budget s'applique à tous les fichiers et écrivains, y compris les instances anciennes. Déclarer la suppression des fichiers orphelins après redéploiement ; la rotation de chaque fichier seul ne borne pas le nombre de fichiers.
- Disque plein, permission refusée ou échec du logger ne DOIVENT PAS faire échouer une transaction métier. Borner la file de journalisation et les attentes, compter les pertes avec `diddi_telemetry_dropped_total`, et prévoir un diagnostic de secours sans récursion du logger.
- Les archives locales constituent un tampon borné, pas une promesse de rétention centrale ni de livraison sans perte. Mesurer le débit pour dimensionner la fenêtre récupérable lors d'une panne du collecteur.
- stdout PEUT être conservé pour le diagnostic local, avec rotation Docker indépendante. Le même événement NE DOIT PAS être envoyé simultanément à Loki par fichier, stdout collecté et OTLP logs. L'export des traces OTLP reste indépendant du transport des logs.

### 4.5 Responsabilités et manifeste de raccordement

Le module fournit : logger JSON, écriture/rotation, droits, montage en lecture/écriture, variables effectivement consommées, modèle de concurrence et tests. DiddiObserve fournit : déclaration du volume externe, montage en lecture seule dans Alloy, règles de lecture et de filtrage, identité issue du registre, positions persistantes, stockage Loki, dashboards et contrôles d'arrivée. Les deux équipes vérifient ensemble la rotation, la reprise et la corrélation.

Le manifeste DOIT déclarer `logs.transport` (`file-jsonl`, `otlp-http` ou transport legacy documenté), hôte de stockage, nom du volume, chemins actifs et d'archives, écrivains, identité de chaque composant, droits requis, seuil et nombre d'archives, budget total, nettoyage des instances anciennes, transport central unique, comportement de reprise et exceptions de confidentialité. Il référence les secrets sans leurs valeurs. Un worker ne reçoit pas automatiquement l'identité `api` parce qu'il partage un volume : ses fichiers doivent être associés à une entrée/composant distincts du registre.

Les [exemples de configuration communs](docs/LOGGING-FILES.md) illustrent le montage ID et la convention pour tous les modules. Ils ne constituent pas une activation de la collecte. En particulier, `observability.jsonl` ne correspond pas au motif historique `*.log` : DiddiObserve DOIT adapter sa règle de lecture avant de déclarer ce raccordement opérationnel.

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

Les métriques et endpoints d’ingestion DOIVENT être privés et authentifiés. TLS est requis sur tout transport hors socket/local explicitement isolé ; les certificats sont vérifiés. Un service ancien sans authentification native peut passer par une passerelle privée authentifiée, à condition que son accès direct soit effectivement bloqué.

Sans authentification valide, la collecte est refusée. Sans configuration de secret, l’endpoint reste fermé ; il ne doit pas devenir public par défaut. Les identifiants de scrape sont propres à chaque service/environnement, révocables et renouvelables. Aucun token utilisateur ou clé d’administration Portainer ne sert de secret de collecte.

DiddiObserve fournit les adresses d'ingestion exactes, un secret d'ingestion distinct du token de scrape et le certificat public de confiance avec son empreinte et sa date d'expiration. Les équipes installent ces paramètres et le certificat dans leurs conteneurs ; elles ne les inventent pas et ne réutilisent pas de secrets métier. Les noms de variables propres aux SDK sont déclarés dans le manifeste. Les clés privées TLS restent côté plateforme. La plateforme n'active un scrape qu'après confirmation du token réellement installé par le producteur. L'accès fichier repose sur les permissions du volume et son montage en lecture seule ; il n'utilise pas le token OTLP.

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
| Rotation fichier applicatif cible | 10 MiB actif + 5 archives par écrivain ; budget total et nettoyage documentés |
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
| C12 | Rétention/rotation configurées, sauvegardes couvertes, règles d’alertes vérifiées et runbooks attribués ; pour les fichiers : preuve de rotation sous charge, reprise après redémarrage, lecture seule Alloy, droits, budget disque et concurrence maîtrisée |

Une simple présence de SDK, un conteneur `running` ou un endpoint `200` ne suffit pas. Le rapport de conformité contient résultats, horodatage, environnement, révision, preuves et exceptions. Les critères non applicables doivent être justifiés. Aucun des services audités n’est certifié par le présent document.

## 13. Versionnement et adoption

La version suit `MAJOR.MINOR.PATCH` : changement incompatible de type, unité ou sémantique → majeur ; ajout compatible → mineur ; correction rédactionnelle → patch. Les consommateurs v1 DOIVENT ignorer les champs supplémentaires inconnus. Une propriété ne doit pas changer silencieusement de sens.

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
