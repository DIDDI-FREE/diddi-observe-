# Pilote synthétique

Le profil opt-in `compose.portainer.synthetic.yaml` ajoute une source `synthetic` dans l’environnement `test`, déploiement `observe-pilot`. Les 15 modules réels restent désactivés. Le conteneur de test n’a aucun port hôte et n’effectue aucun appel métier.

## Activation

Sélectionner ce chemin Compose dans la stack Git existante, sans changer le nom de projet ni supprimer ses volumes. Conserver les variables existantes et ajouter des secrets distincts dans `OTLP_PASSWORDS_JSON` et `METRICS_TOKENS_JSON`, chacun sous la clé `synthetic`.

La passerelle protège les routes OTLP et `POST /synthetic-test` par Basic auth (`synthetic` et le mot de passe OTLP). Cette dernière route accepte uniquement un `trace_id` hexadécimal de 32 caractères, incrémente un compteur et écrit un log de test. Les métriques sont protégées par bearer token. Les fichiers de test sont bornés à environ 2 Mio par rotation.

## Validation

Le script `scripts/smoke.py` peut tester le serveur distant avec :

- `OBSERVE_TEST_URL` : URL HTTPS de la passerelle.
- `OBSERVE_AUTH_FILE` : fichier JSON privé contenant `admin` et `synthetic` (les deux mots de passe).
- `OBSERVE_INSECURE_TLS=1` : uniquement pour le certificat autosigné staging ; désactive explicitement la vérification TLS pendant ce test.

Le fichier d’authentification doit rester hors Git, par exemple dans `test-results/`, ignoré par le dépôt. Ne jamais enregistrer les secrets dans une capture ou un rapport.

Le test vérifie les refus d’ingestion sans bons identifiants, le compteur de l’exercice, la disponibilité, les deux flux de logs, la trace correspondante, l’identité imposée et la suppression des valeurs sensibles synthétiques. Le compteur n’expose pas de trace_id comme label ; seuls les logs et la trace sont liés directement par cet ID.

Le rapport local `test-results/smoke.json` indique la cible, le trace_id, la date et si TLS a été vérifié. Dans Grafana, sélectionner `environment=test` et `service=synthetic`. Les données de test ne constituent pas une preuve de conformité des modules réels.

## Retour au profil normal

Revenir à `compose.portainer.yaml`, reconstruire/recréer les services et retirer uniquement le conteneur synthétique devenu orphelin. Ne pas supprimer les volumes. Les routes de test disparaissent et les données historiques expirent avec les rétentions configurées. Les changements de certificat/domaine et la migration Nginx Proxy Manager restent des opérations distinctes.

Génération reproductible : `python scripts/render.py`, `python scripts/portainer.py`, puis `python scripts/synthetic_profile.py`.
