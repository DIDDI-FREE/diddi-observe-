# Collecte centrale — contrôle du 18 novembre 2026, 12:21 UTC

Prometheus a effectivement scrapé cinq cibles avec authentification et sans erreur : DiddiSend, DiddiGo, DiddiFree ID, DiddiPay et DiddiComms. Les quatre dernières ont été activées aujourd'hui. Les tokens absents/faux ont été refusés, les tokens dédiés valides acceptés. Les secrets sont conservés uniquement dans la configuration privée de DiddiObserve.

DiddiGo, DiddiFree ID, DiddiPay et DiddiComms sont scrappés par IP publique dans le cadre MVP explicitement autorisé ; DiddiSend conserve sa cible fonctionnelle déjà en place. L'exception HTTP est déclarée explicitement et limitée à staging dans le générateur. Aucun module métier n'a été modifié.

Séries canoniques observées au contrôle : DiddiSend 488, DiddiGo 541, DiddiFree ID 159. Ces nombres varient avec le trafic. Les scrapes DiddiPay et DiddiComms sont UP ; la conformité de leurs noms et labels au protocole reste à examiner, ce contrôle ne vaut pas validation de tous leurs dashboards.

## Modules non activés

| Module | Constat | Élément à fournir/corriger par son équipe |
| --- | --- | --- |
| DiddiFiles | `/metrics` répond 200 sans token ; `METRICS_TOKEN` vide | Installer et faire vérifier un token dédié avant activation |
| DiddiSupport | `/metrics` répond 404 ; aucune variable METRICS détectée | Chemin réel et authentification dédiés |
| DiddiMap | `/metrics` répond 404 ; aucune variable METRICS détectée | Chemin réel et authentification dédiés |
| DiddiRecensement | `/metrics` répond 404 ; aucune variable METRICS détectée | Chemin réel et authentification dédiés |
| DiddiFood Radar | `/metrics` répond 404 ; aucune variable METRICS détectée | Chemin réel et authentification dédiés |
| DiddiFood | Backend sans port hôte publié et sans variable METRICS détectée | Endpoint joignable et authentification à déclarer |
| Backoffice | Backend sans port hôte publié et sans variable METRICS détectée | Endpoint joignable et authentification à déclarer |
| Review worker | Conteneurs arrêtés | Déploiement actif et mécanisme de collecte déclaré |
| Pilotage / Radar web | Pas de cible Prometheus applicative identifiée dans cet inventaire | Confirmer profil web-edge ou endpoint réel ; ne pas inventer une cible |

Un 404 sur `/metrics` ne prouve pas l'absence de toute instrumentation : un autre chemin peut exister. Ces modules restent désactivés dans le registre central jusqu'à vérification de leur cible réelle.

## Autres signaux

DiddiGo : logs et traces récents reçus. DiddiFree ID : traces récentes reçues ; son volume `diddifree-id-observability-logs-staging` est monté côté producteur, mais le collecteur central ne le monte pas encore : aucun log ID reçu. L'URL de traces actuellement installée dans ID utilise encore le nom Docker interne ; l'équipe peut appliquer la base publique du protocole sans modifier les identifiants.

Le protocole universel reste la référence : [DIDDI Observability](../DIDDI-Observability-v1.md). Ce fichier est un état opérationnel, pas un protocole par module.
