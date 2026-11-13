# Déploiement Git avec build sur le serveur

Le dépôt contient le Compose, les configurations et un Dockerfile à plusieurs cibles. Portainer clone le dépôt ; Docker construit chaque image avec les fichiers correspondants. Aucun script ne retélécharge Git au démarrage. Aucun chemin `/data/compose/...` n’est monté dans un conteneur.

## Paramètres Portainer

- Environnement : Docker Standalone (`diddifree-prod`), pas Swarm.
- Stack depuis Repository : `https://github.com/DIDDI-FREE/diddi-observe-.git`.
- Référence : `refs/heads/main` (ou version Git choisie).
- Chemin Compose : **`compose.portainer.yaml`**.
- Ne pas coller seulement le YAML dans le Web editor : le build nécessite tout le dépôt.
- Compose doit prendre en charge `build.target`, `pull_policy: build` et `service_completed_successfully`.

Les images sont construites localement et ne sont pas publiées. L’accès à Docker Hub et PyPI est nécessaire pendant le build. Le démarrage des images déjà construites ne nécessite ni Git ni installation de dépendances.

## Variables dans Portainer

| Variable | Valeur / fonction |
|---|---|
| `GRAFANA_ADMIN_PASSWORD` | Obligatoire : mot de passe initial de `admin`. |
| `COMPOSE_PROJECT_NAME` | `diddi-observe` par défaut. Garder cette valeur stable pour conserver les mêmes volumes. |
| `OBSERVE_BIND` | `127.0.0.1` par défaut. `0.0.0.0` pour publier sur les interfaces du serveur, avec pare-feu adapté. |
| `OBSERVE_PORT` | `19443` par défaut. |
| `GRAFANA_ROOT_URL` | URL réellement utilisée, par exemple `https://observe.example.com:19443/`. |
| `OBSERVE_TLS_HOST` | Domaine seul ou IP, sans schéma ni port ; `localhost` par défaut. Utilisé lors de la première génération du certificat staging. |
| `TLS_CERT_PEM`, `TLS_KEY_PEM` | Facultatifs, mais toujours ensemble : certificat PEM et clé PEM avec vrais retours à la ligne. |
| `OTLP_PASSWORDS_JSON` | Facultatif, objet JSON associant l’ID de chaque source OTLP activée à son mot de passe. |
| `METRICS_TOKENS_JSON` | Facultatif, objet JSON associant l’ID de chaque source métriques activée à son jeton existant. |

Exemple de structure uniquement : `{"service-id":"secret-fourni-par-operateur"}`. Ne pas enregistrer les vraies valeurs dans Git. Portainer transmet seulement les variables explicitement déclarées dans `environment`. Les scripts lisent l’environnement du conteneur, sans connexion à l’API Portainer. Les opérateurs ayant accès aux inspections de conteneurs peuvent lire ces variables : ce n’est pas un coffre-fort externe.

Grafana lit directement son mot de passe initial depuis l’environnement. Le service ponctuel `init-storage` prépare les droits des volumes, le certificat et les fichiers d’authentification à partir des variables. Il ne télécharge aucun fichier et n’a pas de réseau. Ses logs n’affichent pas les secrets. Son état « exited (0) » après initialisation est normal.

Sans paire TLS fournie, un certificat autosigné valable 30 jours est créé et conservé dans un volume. Le navigateur affichera un avertissement de confiance. Pour renouveler le certificat ou changer de domaine, fournir une paire PEM valide et recréer `init-storage`, puis redémarrer la passerelle. Modifier seulement `OBSERVE_TLS_HOST` ne remplace pas un certificat existant.

Le mot de passe Grafana est initialisé uniquement lorsque sa base est vierge. Modifier la variable ne change pas le mot de passe d’un compte existant ; utiliser l’interface Grafana ou sa procédure de réinitialisation.

## Mises à jour et stockage

Les configurations et dashboards résident dans les images : mettre à jour Git puis reconstruire/recréer les services. `pull_policy: build` demande le build lors d’un déploiement Compose. Ne pas se limiter à « restart » ou « re-pull images » : ces actions seules ne reconstruisent pas les configurations.

Les volumes de données gardent les noms du profil local pour faciliter la continuité d’une stack existante. Avant de remplacer une stack, vérifier son nom de projet et ses volumes ; ne pas supprimer les volumes. Les secrets TLS et d’ingestion ont leurs propres volumes. Le volume `log-inputs` est vide tant qu’aucune source de fichiers n’y écrit ; il ne collecte pas automatiquement les logs Docker de l’hôte.

Les 15 sources réelles restent désactivées. Pour en activer une : modifier le registre, exécuter `python scripts/render.py` puis `python scripts/portainer.py`, committer les fichiers générés, fournir ses variables d’authentification et préparer l’accès réseau autorisé au service.

Ce correctif résout les fichiers de configuration manquants. Il ne modifie pas les pools réseau de l’hôte : l’épuisement des subnets nécessite le travail réseau séparé déjà discuté.

Référence : [déployer une stack Git dans Portainer](https://docs.portainer.io/user/docker/stacks/add).
