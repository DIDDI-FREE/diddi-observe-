# Validation locale — 13 novembre 2026

Exécutée sur Docker Desktop Linux, uniquement avec le service synthétique du dépôt.

- 11 tests unitaires de configuration : réussis.
- Génération reproductible : `scripts/render.py --check` réussi.
- Validation native Prometheus, Loki, Tempo et Nginx : réussie.
- Démarrage réel Alloy, Grafana et backends : réussi.
- Test `scripts/smoke.py` : réussi, avec TLS vérifié et authentification.
- Ingestion sans authentification ou avec mauvais mot de passe : rejetée.
- Scrape Prometheus authentifié et probe readiness : réussis.
- Logs fichiers et OTLP retrouvés dans Loki avec identifiant de trace commun.
- Trace retrouvée dans Tempo ; fausse identité remplacée et attribut sensible supprimé.
- Valeur sensible de test absente des deux flux de logs relus.
- Six dashboards et quatre règles d’alerte provisionnés via API Grafana.

Le rapport détaillé local est dans `test-results/smoke.json`, exclu de Git.
La CI est configurée pour répéter ces contrôles ; cette note ne présume pas son résultat distant.

Restent à qualifier au déploiement : accès et données des vrais modules, rendu visuel en situation réelle, notifications externes, restauration des sauvegardes, charge, pannes prolongées et critères C01–C12. Aucun déploiement Portainer n’a été effectué.
