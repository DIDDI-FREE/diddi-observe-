# Exploitation DiddiObserve

## Source absente ou indisponible

1. Vérifier l’état du registre et les signaux explicitement activés.
2. Examiner Targets dans Prometheus via la source Grafana et les logs du collecteur.
3. Distinguer erreur réseau/TLS, refus d’authentification, readiness défaillante et silence applicatif.
4. Contacter le propriétaire du service. Ne pas redémarrer un autre module depuis cette stack.

## Logs ou traces absents

Vérifier la route HTTPS, les identifiants du service et les rejets Alloy/Loki. Vérifier la cohérence de l’environnement et la plage de temps UTC. Une trace peut être non échantillonnée. Le tableau de bord Logs sépare les labels des sources fichiers et OTLP. Ne jamais remplacer l’absence de données par des zéros.

## Saturation et panne du collecteur

Observer files, erreurs d’export, mémoire et disque de l’hôte. Les files d’export Alloy sont persistantes et bornées ; les reprises ont un budget de cinq minutes. Au-delà, une perte est possible. Éviter tout redémarrage en boucle. Réduire la collecte bruyante de manière tracée et vérifier que les producteurs métier continuent de fonctionner.

## Alertes

Quatre règles initiales : scrape en échec, readiness négative, source métriques attendue absente et pertes de télémétrie. Le destinataire `local-only` reçoit uniquement dans la stack. Pour activer une notification externe, faire valider le canal, la destination et un test, puis modifier `config/grafana/alerting/routing.yaml` avec un secret externe.

Les alertes de heartbeat/backlog nécessitent les cadences du manifeste ; les alertes d’erreur/latence nécessitent les SLO. Les panneaux existent, mais aucun seuil universel n’est inventé.

## Sauvegarde et restauration

Sauvegarder Git, les secrets via un coffre distinct, et les volumes selon le niveau de conservation voulu. Pour un premier backup cohérent monohôte, planifier une fenêtre, arrêter **uniquement** le projet DiddiObserve sans `-v`, puis sauvegarder ses volumes identifiés par le label Compose de ce projet. Ne jamais faire un arrêt global de Docker.

Restaurer dans un projet de test séparé avec les mêmes versions d’images et les configurations correspondantes. Remettre les UID/GID attendus sur les fichiers, démarrer les backends puis le collecteur et Grafana. Vérifier une requête historique, les dashboards, l’authentification et un nouveau signal synthétique. Mesurer et documenter RPO/RTO avant production. La stack ne crée pas de sauvegarde automatique dans un stockage non fourni.

## Mise à jour et retour arrière

Versions d’images explicites. Avant mise à jour : lire les changements incompatibles, sauvegarder, tester en projet isolé et exécuter le smoke. Les migrations internes des backends peuvent rendre un downgrade impossible ; restaurer les volumes d’avant migration plutôt que d’utiliser arbitrairement une ancienne image sur un volume migré.

Un changement de certificat ou htpasswd nécessite de recharger/recréer la passerelle. Le bootstrap ne fait pas de rotation et n’écrase jamais un secret existant. Supprimer les anciens credentials seulement après validation des nouveaux producteurs.
