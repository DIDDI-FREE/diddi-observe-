# Migration des intégrations 1.x vers le protocole commun 2.0.0

Seule référence normative : [protocole universel](../../DIDDI-Observability-v1.md), sections 2, 4.3 et validation de conformité.

- Producteurs OTLP HTTP/protobuf existants : conserver leurs secrets et endpoints fonctionnels, vérifier les variables, le schéma, chaque processus et les preuves de réception ; ne pas réimplémenter le métier.
- Producteurs par fichier, stdout collecté ou autre transport : ajouter l'export OTLP au logger, valider un événement canari exclu de l'ancien transport, coordonner la bascule, vérifier la réception puis retirer l'ancienne collecte centrale.
- Pas de double export général pour « tester » : il crée des doublons. Documenter la fenêtre de bascule et le retour arrière.
- Ne pas supprimer les fichiers/volumes du producteur ni importer les archives automatiquement.
- Un transport historique temporairement maintenu doit déclarer un responsable, une échéance et migration_required=true. Il ne vaut pas conformité 2.0.0.
- La version du schéma des événements reste 1.0.0. La version du protocole réellement adoptée n'est relevée à 2.0.0 qu'après validation.
- Les politiques de rétention et l'exception OTP staging ne sont pas modifiées par cette migration.
