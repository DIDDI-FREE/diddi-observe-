# Remise aux équipes — observabilité MVP staging

Référence actuelle : protocole v1.1.3, schéma des événements 1.0.0. Mise à jour du 17 novembre 2026.

## Connexion retenue

L'ingestion est publique par IP : `http://169.58.70.37:19480`. Pas de domaine à attendre, pas de CA ni de certificat client à installer, pas de réseau Docker partagé requis pour envoyer les logs et traces. HTTP ne chiffre pas le trafic ni les identifiants en transit. HTTPS sera une évolution ultérieure.

Chaque module reçoit ses propres identifiants OTLP et son propre token de métriques. Ne jamais copier les secrets de DiddiSend ni réutiliser un secret métier. Les valeurs sont remises séparément dans `secrets/onboarding/<service>.env`, hors Git. Les champs secrets vides des JSON ne doivent pas effacer les valeurs installées.

## Marche à suivre

1. Lire le contrat JSON et le guide propres au module. Les noms des variables doivent être réellement pris en charge par son SDK et son Compose.
2. Installer/configurer l'export OTLP HTTP/protobuf des traces et logs, avec traitement par lots, délais bornés et arrêt propre. Une panne de télémétrie ne doit pas faire échouer une opération métier.
3. Reporter les variables fournies dans Portainer et redéployer les processus concernés. Une variable uniquement définie dans Portainer, sans passage par Compose ni lecture par le code, n'active rien.
4. Produire une requête non destructive et un événement de test identifié, puis demander à DiddiObserve de confirmer leur réception dans Loki et Tempo.
5. Valider séparément les métriques : route protégée, token dédié et activation du scrape central. Logs/traces fonctionnels ne signifient pas que les métriques sont raccordées.

Le chemin générique `/otlp/<service>` sert de base : l'exporteur ajoute `/v1/traces`. La route de logs exacte est `/otlp/<service>/v1/logs`. Les requêtes sont POST avec authentification. Un navigateur GET peut recevoir 404 sur la base et 403 sur une route d'ingestion : cela ne démontre pas une panne. Ne pas copier des espaces ou du balisage Markdown dans les variables.

## État vérifié

- **DiddiSend** : API saine ; logs et traces réellement retrouvés après le redéploiement du 17 novembre (20 entrées et 4 traces dans les requêtes de vérification). Scrape central des métriques encore désactivé.
- **DiddiGo** : prochain module. La stack est saine ; le code local inspecté contient des événements JSON console et `/metrics`, mais pas d'export OTLP identifié. L'équipe doit implémenter le raccordement décrit dans son guide. Ne pas déclarer le producteur connecté sur la seule existence d'une route centrale.
- **DiddiFree ID** : contrat spécifique conservé, avec logs fichier JSONL ; ne pas imposer ce transport aux autres modules. La décision temporaire OTP reste distincte.

## Documents à transmettre

- DiddiGo : [guide](DIDDIGO-HANDOFF.md) et [contrat JSON](teams/diddigo.json).
- DiddiSend : [guide validé](DIDDISEND-HANDOFF.md) et [contrat JSON](teams/diddisend.json).
- DiddiFree ID : [migration](teams/MIGRATION-V1.md) et [contrat JSON](teams/diddifree-id.json).
- Tous : [protocole](../DIDDI-Observability-v1.md).

Les anciennes instructions de CA privée, d'attente de HTTPS ou d'ingestion réservée au réseau Docker sont remplacées par cette remise. Les équipes modifient leurs modules ; DiddiObserve configure sa plateforme centrale.
