# diddi-observe-

Plateforme centrale d’observabilité DIDDI : Grafana, Prometheus, Loki, Tempo et Alloy, avec une passerelle TLS authentifiée, un registre de services et six dashboards provisionnés.

**Le dépôt prépare le déploiement. Aucun service Portainer n’est raccordé ou modifié automatiquement.** Les quinze entrées applicatives du registre sont désactivées par défaut. Le pilote local utilise exclusivement des données synthétiques.

## Démarrage local

Prérequis : Docker Engine + Compose v2 ou supérieur, Python 3.11+, environ 6 Go de RAM disponibles pour la stack et de l’espace pour les images/volumes.

```sh
python -m pip install -r requirements-dev.txt
python scripts/bootstrap.py --demo
docker compose -f compose.yaml -f compose.demo.yaml up -d --build
python scripts/smoke.py
```

Ouvrir **https://localhost:19443**. Compte `admin`, mot de passe dans `secrets/grafana_admin`. Le certificat local est autosigné et valable trente jours ; l’outil smoke le vérifie explicitement. Ne jamais utiliser ces certificats de démonstration pour un déploiement distant.

Arrêter uniquement cette stack, sans supprimer les volumes :

```sh
docker compose -f compose.yaml -f compose.demo.yaml down
```

Pour démarrer sans données synthétiques : `docker compose -f compose.yaml up -d --build`. Après une démonstration, arrêter d’abord la stack avec les deux fichiers pour retirer aussi le conteneur synthétique. Les données de test restent dans les volumes ; utiliser un nouveau nom de projet pour un environnement vierge.

## Dashboards

- **Plateforme** : inventaire, couverture de collecte, disponibilité, trafic et p95 lorsqu’il existe.
- **Service** : routes, erreurs, latences et dépendances.
- **Logs** : flux fichiers et OTLP, recherche et lien vers les traces.
- **Traces** : recherche TraceQL et investigation dans Explore.
- **Workers et files** : heartbeat, backlog, âge et dead letters.
- **Santé de la collecte** : composants centraux, mémoire, exports et pertes.

Les tableaux de bord affichent « Aucune donnée » lorsque la source n’est pas raccordée. Le registre ne confond pas une collecte configurée avec une conformité démontrée.

## Organisation

```text
registry/services.json       sources, propriétaires, capacités, états
scripts/render.py           génération contrôlée des configs de collecte
generated/                  configs reproductibles, sans secrets
config/                     backends, sources Grafana et alerting
dashboards/                 six dashboards JSON
app/                        exporteur d’inventaire et fixture synthétique
scripts/bootstrap.py        secrets et certificat locaux, jamais écrasés
scripts/smoke.py            test réel de la chaîne TLS → backends → Grafana
tests/                      garde-fous de configuration
docs/                       déploiement, raccordement, exploitation
DIDDI-Observability-v1.md    contrat commun des services
```

## Vérification

```sh
python -m unittest discover -s tests -v
python scripts/render.py --check
docker compose -f compose.yaml -f compose.demo.yaml config --quiet
python scripts/smoke.py
```

`python scripts/dashboards.py` régénère les dashboards, les sources Grafana et l’alerting. Toute modification du registre impose `python scripts/render.py`, revue des fichiers générés et tests avant activation.

## Sécurité et état du produit

Seule la passerelle est publiée, sur loopback par défaut. Prometheus, Loki, Tempo et Alloy n’ont aucun port hôte. Les backends non authentifiés sont confinés au réseau Docker interne ; seul le collecteur, les opérateurs Grafana et la passerelle doivent pouvoir y accéder. L’ingestion OTLP est authentifiée par source avec des identifiants distincts et une identité imposée par le collecteur.

Les alertes sont envoyées à un **récepteur local sans redistribution** : aucun email, Slack ou webhook externe n’est configuré. Les destinations réelles seront choisies au déploiement.

Cette livraison est une base monohôte de staging. La haute disponibilité, le stockage objet de production, l’isolation forte entre équipes, les quotas disque hôte et la certification C01–C12 de chaque module ne sont pas acquis. Les données libres des applications doivent déjà être nettoyées à la source : les filtres du collecteur sont une seconde défense, pas un détecteur universel de secrets.

Voir [le déploiement](docs/DEPLOYMENT.md), [le raccordement d’un service](docs/ONBOARDING.md), [le runbook](docs/RUNBOOK.md) et [les décisions techniques](docs/DECISIONS.md).
