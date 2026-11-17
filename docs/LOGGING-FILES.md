# Logs JSON sur volume partagé — guide commun v1.1

Référence normative : [DIDDI Observability v1.1.1](../DIDDI-Observability-v1.md), sections 4.3 à 4.5. Ce guide prépare la configuration ; il ne modifie aucune stack.

## Ce qui est commun et ce qui change

Tous les modules utilisent la même variable `OBSERVABILITY_LOG_FILE`, le même schéma JSON et les mêmes règles de rotation. Le nom du volume et l'identité sont propres au module/environnement/déploiement. L'implémentation du logger dépend du langage et du nombre de processus ; il n'existe pas de fragment Python/Node universel.

Le changement se situe dans l'initialisation du logger et le Compose. Les appels de journalisation existants continuent à fonctionner ; les routes métier n'ouvrent pas elles-mêmes de fichiers.

## Côté producteur : exemple DiddiFree ID

Variables de la stack ID dans Portainer :

```ini
OBSERVABILITY_LOG_FILE=/var/log/diddifree/observability.jsonl
OBSERVABILITY_LOG_VOLUME_NAME=diddifree-id-observability-logs-staging
```

À fusionner dans le Compose existant, sans remplacer les autres variables ou volumes :

```yaml
services:
  app:
    environment:
      OBSERVABILITY_LOG_FILE: ${OBSERVABILITY_LOG_FILE:-/var/log/diddifree/observability.jsonl}
    volumes:
      - observability-logs:/var/log/diddifree

volumes:
  observability-logs:
    name: ${OBSERVABILITY_LOG_VOLUME_NAME:?Définir le volume de logs}
```

Le nom réel du service Compose remplace `app` pour les autres modules. Compose crée le volume nommé s'il n'existe pas. Le responsable configure les droits du répertoire pour l'utilisateur applicatif et le lecteur Alloy ; le montage seul ne garantit pas ces droits.

Le logger doit lire la variable, écrire les événements déjà nettoyés en JSON UTF-8 par ligne, faire tourner le fichier au seuil de 10 MiB et conserver au plus 5 archives par écrivain. Ce sont des valeurs de référence à programmer dans la bibliothèque ou à exposer via des réglages documentés ; définir la variable de chemin n'ajoute pas automatiquement un handler ni une rotation.

En cas de plusieurs processus, ne pas attacher plusieurs handlers de rotation indépendants au même fichier. Utiliser un écrivain unique avec file bornée ou des fichiers distincts par composant/instance. Déclarer alors les chemins réels et le nettoyage des anciennes instances. Le budget initial d'environ 60 MiB par écrivain doit être multiplié par leur nombre, avec une marge pour le dépassement par événement.

stdout peut rester activé, avec sa propre rotation Docker, à condition de ne pas collecter deux fois les mêmes événements au centre. Choisir fichier **ou** OTLP logs pour chaque source ; conserver OTLP traces dans les deux cas.

## Côté DiddiObserve

Après création et vérification du volume sur le même hôte Docker, l'équipe centrale ajoute :

```yaml
services:
  alloy:
    volumes:
      - id-observability-logs:/var/log/inputs/diddifree-id:ro

volumes:
  id-observability-logs:
    external: true
    name: diddifree-id-observability-logs-staging
```

Ce montage ne change pas le module producteur. Alloy lit le fichier actif `/var/log/inputs/diddifree-id/observability.jsonl`, conserve ses positions dans son stockage propre et attribue l'identité validée du registre. Un motif borné peut être utilisé pour plusieurs fichiers actifs ; les archives ne doivent pas être incluses automatiquement.

**Limite actuelle du générateur :** le profil fichier historique utilise `/var/log/inputs/<id>/*.log`. Il ne lit pas automatiquement `.jsonl`. L'ajout du montage, l'adaptation du chemin de lecture et la validation du rendu Alloy sont nécessaires avant activation. Le profil central de raccordement ID/Send n'a pas encore de montage de ce volume : les routes OTLP préparées ne constituent pas une preuve de collecte fichier.

Un volume externe absent doit être préparé côté producteur avant le déploiement du consommateur. Ne pas créer silencieusement un volume vide sous un autre nom pour masquer ce problème. Aucun socket Docker n'est nécessaire. Si les stacks sont sur deux hôtes, utiliser un transport réseau déclaré plutôt que supposer qu'un nom identique partage le stockage.

## Manifeste à remettre

Exemple descriptif, à compléter ; **ce n'est pas un remplacement direct de `registry/services.json`**, dont le schéma est interne à DiddiObserve :

```yaml
logs:
  transport: file-jsonl
  volume_name: diddifree-id-observability-logs-staging
  docker_environment: diddifree-prod
  environment: staging
  deployment_id: diddifree-id-staging
  active_files:
    - path: /var/log/diddifree/observability.jsonl
      registry_id: diddifree-id
      component: api
  writer_model: single-writer  # À confirmer selon le déploiement réel
  rotation:
    max_bytes: 10485760
    backup_count: 5
    strategy: rename-and-reopen
  permissions: to-be-confirmed
  total_disk_budget_bytes: to-be-confirmed
  orphan_cleanup: to-be-confirmed
  initial_read_position: to-be-agreed
  restart_recovery: to-be-tested
  central_duplicate_transport: false
  owner_contact: to-be-confirmed
```

Le worker `account-purger` doit déclarer ses propres fichiers et son identité/composant, ou utiliser un dispositif central d'écriture explicitement validé. Ne pas attribuer l'identité API à ses événements par défaut.

## Validation avant activation

1. Produire des événements synthétiques : succès, exception et contexte de trace ; vérifier JSON, UTC, identité et absence de secrets hors exception documentée.
2. Vérifier l'écriture sous l'utilisateur réel du conteneur et la lecture depuis Alloy en lecture seule.
3. Déclencher une rotation sur un environnement de test, poursuivre l'écriture, puis vérifier l'arrivée des nouveaux événements dans Loki sans relecture massive des archives.
4. Redémarrer producteur et collecteur : démontrer la reprise des positions, mesurer pertes/doublons éventuels et vérifier le nettoyage des fichiers d'instances anciennes.
5. Tester les limites de disque et les erreurs de permissions de manière isolée : l'activité métier reste possible et les pertes sont signalées.
6. Vérifier la corrélation dans Grafana puis renseigner les preuves dans le registre. Un volume présent ou un fichier créé ne suffit pas à déclarer `connected`.

L'exception temporaire OTP de DiddiFree ID staging et son interrupteur restent régis par la section 4.2 du protocole. Ni désactivation silencieuse ni transfert rétroactif implicite ; aucun véritable OTP n'est nécessaire aux tests.
