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

## Panne contrôlée et retour au service

Le 13 novembre 2026, seul `diddi-observe-synthetic-1` a été arrêté via Portainer, puis redémarré. Les heures ci-dessous sont en UTC.

- 17:50:22 : contrôle préalable, scrape et readiness à `1`, quatre règles inactives.
- 17:51:20 : les deux alertes du pilote passent en attente ; scrape et readiness à `0`.
- 17:53:20 : `target-down` et `readiness-down` passent à `firing`, avec les labels `service_name=synthetic`, `environment=test` et `deployment_id=observe-pilot`.
- Avant 17:53:56 : le récepteur local du registre journalise deux événements `observe.alert.received` (3537 et 3370 octets).
- 17:54:03 : pilote redémarré et état Docker `running` confirmé.
- 17:54:43 : scrape et readiness revenus à `1` ; `target-down` inactive.
- 17:55:20 : `readiness-down` également inactive. Les quatre règles sont revenues à l'état inactif.

La chronologie machine est conservée localement dans `test-results/alert-validation.jsonl` (hors Git). La réception locale est attestée par les logs ; le récepteur ne journalise pas le contenu des notifications, donc leur contenu et une notification de résolution ne sont pas certifiés par ce test. La résolution est vérifiée dans l'API des règles Grafana. Aucun canal de notification externe n'a été sollicité. Même limite TLS autosigné que pour le test précédent.

## Périmètre restant

Les 15 modules réels restent désactivés. Aucun SLO métier ou conformité C01–C12 n’est déclaré. Les notifications externes, la validation visuelle interactive et la restauration des sauvegardes restent à réaliser.

Le conteneur `synthetic` reste disponible pour rejouer un test ; il ne génère pas de trafic métier ni de charge continue. Les métriques de requêtes représentent seulement les exercices explicitement exécutés, pas du trafic réel.
