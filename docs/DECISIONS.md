# Décisions techniques

- Plan et protocole approuvés avant implémentation. Aucun frontend métier personnalisé : Grafana assure les vues communes et Explore.
- Versions sélectionnées depuis les releases officielles lors de la préparation : Grafana 13.3.1, Loki 3.7.10, Tempo 3.1.1, Alloy 1.21.3, Prometheus 3.16.0, Blackbox Exporter 0.29.1, Nginx 1.31.8.
- Tempo est en mode monolithique local pour le pilote. La configuration est vérifiée avec le binaire 3.x ; le stockage objet et une éventuelle architecture distribuée seront des décisions de production.
- Réseau interne et aucun port backend publié. Le réseau de collecte de services distants reste à préparer explicitement au déploiement.
- Seule la passerelle rejoint aussi un réseau frontend, nécessaire à la publication du port TLS sur Docker Desktop.
- La file persistante OTLP utilise `otelcol.storage.file`, encore en public preview dans Alloy 1.21.3 ; ce niveau est activé explicitement. Sa tenue aux pannes prolongées doit être qualifiée avant production.
- Identité OTLP imposée par route authentifiée et receiver distinct. Cela évite de faire confiance à un en-tête ou attribut service fourni par le client.
- Exporteur de registre minimal Python standard library. Il n’exécute aucune action sur les services et ne contient pas de credentials.
- Alertes locales seulement ; pas de messages externes non autorisés.
- Aucun accès Docker automatique, aucun branchement aux URLs publiques observées dans l’audit, aucun secret présent dans Git.
- Les plafonds et rétentions du profil staging sont initiaux, pas une garantie de capacité ou disponibilité production.

Références : [OTLP](https://opentelemetry.io/docs/specs/otlp/), [Alloy receiver OTLP](https://grafana.com/docs/alloy/latest/reference/components/otelcol/otelcol.receiver.otlp/), [Loki cardinalité](https://grafana.com/docs/loki/latest/get-started/labels/cardinality/), [Tempo monolithique](https://grafana.com/docs/tempo/latest/reference-tempo-architecture/deployment-modes/), [Grafana provisioning](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/file-provisioning/).
