# Message à transmettre à l'équipe DiddiFreeID

Nous uniformisons tous les modules sur le protocole DIDDI Observability 2.0.0 :
logs et traces en OTLP HTTP/protobuf, métriques en scrape Prometheus authentifié.
Référence unique : [protocole universel](../../DIDDI-Observability-v1.md).
[Paramètres cibles sans secrets](diddifree-id.json).

Merci de migrer les logs API et worker vers OTLP en raccordant les loggers existants,
sans réécrire les routes ou règles métier et sans changer le schéma des événements.

Paramètres communs aux deux processus :
- OTEL_SERVICE_NAME=diddifree-id
- OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
- OTEL_LOGS_ENABLED=true
- OTEL_ENABLED=true si cet interrupteur global commande l'initialisation
- OTEL_EXPORTER_OTLP_ENDPOINT=https://logs-otel.diddifree.com/otlp/diddifree-id
- OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://logs-otel.diddifree.com/otlp/diddifree-id/v1/logs
- OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://logs-otel.diddifree.com/otlp/diddifree-id/v1/traces
- OTEL_EXPORTER_OTLP_HEADERS : conserver le secret dédié fourni, sans le publier.

HTTPS utilise les autorités publiques standard, sans CA privée à monter.
Les endpoints HTTP staging déjà fonctionnels restent acceptés ; ne pas changer les URL
des traces comme effet secondaire obligatoire de cette migration. Les JSON gardent la
base HTTP existante ; les URL HTTPS ci-dessus sont l'équivalent disponible.

Distinguer diddi.component=api et diddi.component=worker dans les ressources ;
conserver deployment.environment.name=staging et diddi.deployment.id=diddifree-id-staging.
Faire passer les variables Portainer dans le Compose et les settings de chaque processus.
Déclarer les éventuels alias de variables, ne pas supposer qu'une variable configure le SDK seule.

Exporter en arrière-plan par lots avec files et délais bornés, arrêt propre et erreurs
d'export sans boucle de logging. La panne de DiddiObserve ne doit pas bloquer le métier.
Tester les vrais loggers après initialisation du serveur : messages JSON et texte,
propagation, niveaux et absence de double handler.

Conserver les métriques et leur METRICS_AUTH_TOKEN actuels ; aucune rotation de secret.
L'exception OTP staging reste inchangée : otp.code et otp.recipient autorisés,
sans autoriser d'autres secrets. Valider le traitement central OTLP sur un événement
synthétique avant la bascule ; ne pas envoyer de vrais OTP dans les preuves partagées.

Ne pas activer l'export général OTLP tant que la collecte fichier centrale tourne :
coordonner une bascule avec DiddiObserve. D'abord un marqueur canari exclu du fichier,
puis désactivation centrale des sources fichier et activation OTLP, avec retour arrière
prévu. Fournir le SHA déployé, le responsable, la date de bascule et les marqueurs API/worker.
DiddiObserve vérifiera dans Loki les deux composants, les identités et l'absence de doublons,
puis retirera son montage du volume partagé. Les fichiers locaux peuvent rester pour dépannage.

Ne déclarer la conformité 2.0.0 qu'après vérification effective des signaux applicables.
