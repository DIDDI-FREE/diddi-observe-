# Migration vers le protocole universel v1.2.1

Appliquer [le protocole universel, section 2](../../DIDDI-Observability-v1.md#2-architecture-et-transports). Cette page décrit seulement la compatibilité avec les intégrations existantes.

- Le schéma des événements reste 1.0.0. Conserver les noms de métriques, les identités et les secrets existants.
- Les nouveaux raccordements utilisent les variables communes ; les modules existants peuvent conserver des alias explicitement documentés. Ne pas réécrire une intégration fonctionnelle uniquement pour renommer une variable.
- DiddiSend conserve ses variables et son export OTLP logs/traces déjà validé.
- DiddiFree ID conserve `METRICS_AUTH_TOKEN` comme alias de `METRICS_BEARER_TOKEN`, `DIDDI_DEPLOYMENT_ID` comme alias de `DEPLOYMENT_ID`, son interrupteur `OTEL_ENABLED` et son endpoint complet `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT`. Son profil de logs fichier JSONL reste compatible ; ne pas changer la décision OTP dans cette migration.
- DiddiGo doit implémenter les règles communes ; son diagnostic est dans sa fiche. Les paramètres seuls ne remplacent pas le code et le passage Compose manquants.
- HTTP public par IP reste accepté pour le MVP. HTTPS public est disponible avec les mêmes chemins ; aucune bascule automatique des producteurs ni installation de CA privée.
- Les métriques, logs, traces et sondes sont validés séparément selon la section 2.4. Mettre à jour la version de conformité uniquement après les vérifications applicables.
