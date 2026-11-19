# Paramètres de raccordement DiddiPay

Référence normative : [standard universel](../../DIDDI-Observability-v1.md).
Ce document contient uniquement les paramètres et l'état opérationnel.

État au 19 novembre 2026 : configuration centrale préparée, mais non déployée.
Accès Portainer MCP et navigateur indisponibles (Transport closed).
Scrape métriques service-diddipay vérifié UP, sans erreur.
Aucune réception applicative de logs/traces n'est déclarée validée.

- Service : diddipay ; environnement : staging ; déploiement : diddipay-staging.
- Base : https://logs-otel.diddifree.com/otlp/diddipay
- Logs : https://logs-otel.diddifree.com/otlp/diddipay/v1/logs
- Traces : https://logs-otel.diddifree.com/otlp/diddipay/v1/traces
- Transport : OTLP HTTP/protobuf.
- Ressources : diddi.component=api ou worker selon le processus.
- Aucun volume partagé, socket Docker ou CA privée.
- Métriques : conserver /internal/metrics et le token existant.

Les variables et le secret OTLP dédié sont préparés dans le fichier local privé
secrets/onboarding/diddipay.env, exclu de Git. Ne pas activer l'export avant vérification des routes centrales.
Les champs publics sans secrets sont dans [diddipay.json](diddipay.json).

## Activation côté plateforme

1. Relire la configuration actuelle de la stack centrale.
2. Fusionner l'entrée privée secrets/onboarding/diddipay-central-entry.json dans
   OTLP_PASSWORDS_JSON sans remplacer les autres entrées ni les autres variables.
   Si une entrée diddipay existe déjà, comparer et réconcilier avant toute modification ;
   ne pas effectuer de rotation implicite.
3. Redéployer uniquement la stack centrale depuis Git.
4. Vérifier chaque route : absence d'identifiant refusée, identifiant d'un autre service refusé,
   identifiant dédié accepté. Un POST vide valide la route, pas le producteur.
5. Vérifier un événement canari et une trace synthétique avec identités API/worker ;
   contrôler que le collecteur conserve la distinction des composants.
6. Après déploiement par l'équipe du module, vérifier de vrais événements et traces,
   puis actualiser les preuves et le JSON de remise.

Aucun paiement ou autre opération métier ne doit être déclenché par ces contrôles.
