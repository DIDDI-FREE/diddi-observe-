# Validation du pilote — 13 novembre 2026

Test effectué sur la stack distante `diddi-observe`, après activation du profil synthétique par variables Portainer. Les autres stacks n’ont pas été modifiées.

## Résultats observés

- Six dashboards Grafana et quatre règles d’alerte provisionnés.
- Six cibles centrales Prometheus à `up=1`.
- Scrape authentifié de `synthetic` à `up=1` et probe readiness à `probe_success=1`.
- Exercice synthétique comptabilisé dans les métriques HTTP.
- Même identifiant retrouvé dans un log fichier JSON, un log OTLP et une trace Tempo.
- Identité falsifiée remplacée par `synthetic` dans la trace.
- Attributs sensibles synthétiques retirés ; sentinelle absente des deux flux de logs relus et de la trace.
- Ingestion sans authentification et avec mauvais mot de passe refusée (HTTP 401).
- Identités du registre préservées ; la règle « source métriques absente » ne retourne aucune source manquante après raccordement du pilote.
- Configuration du lien Loki → Tempo présente et expression de capture du trace_id vérifiée.

Exécution réussie : **2026-11-13 17:46:20 UTC**. Identifiant de trace : `f5ed0e34c3fcd89d18917f22045e4b0d`.

Le rapport machine local est `test-results/smoke.json` (hors Git). La vérification TLS était explicitement désactivée pour ce test distant avec certificat autosigné ; cette validation ne certifie donc pas l’identité TLS du serveur. L’authentification applicative et les contrôles d’ingestion ont été testés.

## Correction apportée pendant la validation

Le scrape de l’exporteur de registre écrasait les labels des services par ceux du collecteur. `honor_labels` est maintenant activé uniquement pour cet exporteur interne de confiance. Les séries antérieures peuvent rester visibles temporairement dans la fenêtre de recherche Prometheus, et restent consultables dans l’historique.

## Périmètre restant

Les 15 modules réels restent désactivés. Aucun SLO métier ou conformité C01–C12 n’est déclaré. Le déclenchement et la résolution d’une alerte par panne contrôlée, les notifications externes, la validation visuelle interactive et la restauration des sauvegardes restent à réaliser.

Le conteneur `synthetic` reste disponible pour rejouer un test ; il ne génère pas de trafic métier ni de charge continue. Les métriques de requêtes représentent seulement les exercices explicitement exécutés, pas du trafic réel.
