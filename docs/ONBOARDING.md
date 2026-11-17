# Raccorder un service

Le protocole commun est [DIDDI Observability v1.1.1](../DIDDI-Observability-v1.md). Chaque module fournit son manifeste, son propriétaire et les preuves locales avant raccordement. Le registre de base garde les sources réelles désactivées ; les activations autorisées du profil central sont décrites dans [ONBOARDING-READY.md](ONBOARDING-READY.md).

## Inscription

Modifier une entrée de `registry/services.json` ou en créer une pour chaque composant/déploiement. L’`id` est unique et stable ; un worker peut partager le `name` du service mais possède son propre `id` et `component=worker`. Renseigner le propriétaire et l’environnement exact.

- `metrics.enabled=true` exige une `url` privée, `auth=bearer` et un token existant dans `secrets/<id>.metrics`.
- `health.enabled=true` exige une URL de readiness accessible au collecteur. Les endpoints de readiness authentifiés nécessitent un module blackbox dédié avant activation ; le profil livré concerne les sondes privées sans secret applicatif.
- `otlp.enabled=true` crée deux routes HTTPS exactes : `/otlp/<id>/v1/traces` et `/otlp/<id>/v1/logs`.
- `logs.enabled=true` active la lecture de `/var/log/inputs/<id>/*.log`, montée depuis `runtime/inputs/<id>`. Cette source peut être remplacée par un montage **en lecture seule**, explicitement autorisé, de fichiers applicatifs JSON. Les logs Docker bruts multiplexés ou les enveloppes json-file ne sont pas des logs applicatifs directement compatibles.

Pour le profil commun **fichier JSON rotatif partagé**, suivre [LOGGING-FILES.md](LOGGING-FILES.md) : le module écrit dans un volume dédié, Alloy monte ce même volume externe en lecture seule. Le chemin standard `observability.jsonl` exige une adaptation explicite du motif historique `*.log` dans le générateur ; activer seulement `logs.enabled` ne suffit pas. Le montage fichier ID n'est pas encore déployé par la publication de cette convention. Les traces OTLP restent indépendantes ; ne pas doubler la collecte des mêmes logs par fichier et OTLP.

Puis :

```sh
python scripts/render.py
python scripts/bootstrap.py
python -m unittest discover -s tests -v
```

Le bootstrap génère des identifiants d’ingestion, mais **ne suppose jamais qu'un nouveau token de scrape est déjà installé dans un service existant**. La plateforme peut préparer un token dédié et le remettre au propriétaire ; celui-ci l'installe, puis confirme avant activation du scrape. Les secrets centraux et la confiance TLS d'ID/Send sont décrits dans [ONBOARDING-READY.md](ONBOARDING-READY.md). Les fichiers de mots de passe et de secrets ne doivent jamais être joints à un ticket ou committés.

Le test `test_real_services_disabled` protège le profil initial : lors d’une activation réelle autorisée, adapter ce test à un registre de référence désactivé et ajouter un test spécifique des cibles autorisées. Ne pas supprimer simplement le garde-fou.

## OTLP

Endpoint générique HTTP du service : `https://<domaine>/otlp/<id>`. Le SDK ajoute `/v1/traces` ou `/v1/logs`. Pour un endpoint spécifique, fournir le chemin complet. Le SDK doit utiliser un en-tête Authorization Basic correspondant à `<id>` et son secret ; l’encodage base64 ne remplace pas TLS. Ne pas réutiliser les identifiants d’un service pour un autre.

La passerelle accepte uniquement POST sur ces routes. Chaque route mène à un receiver Alloy distinct ; le processeur impose nom, environnement, déploiement et composant depuis le registre, indépendamment des valeurs fournies par le client. Aucun receiver Alloy n’est publié sur l’hôte. Version et instance restent renseignées par le producteur.

Les protocoles OTLP HTTP protobuf et JSON sont acceptés par le receiver ; le test utilise JSON pour éviter une dépendance SDK. L’export OTLP de métriques et gRPC ne sont pas exposés dans cette livraison : les métriques utilisent Prometheus, les traces HTTP.

## Logs et confidentialité

La voie fichier prend en charge JSON par ligne et les horodatages `timestamp`, `ts` ou `at`. Une ligne non JSON est rejetée. Le timestamp reste celui de la collecte si aucun horodatage valide ne peut être extrait : ce n’est pas une preuve de conformité v1 du producteur. Les labels sont attribués depuis le registre, pas depuis le corps du log ; les identifiants de requête restent dans le contenu.

Le filtre fichier masque certaines valeurs sensibles dans des champs JSON nommés. Le pipeline OTLP retire des attributs sensibles simples. Ces filtres ne couvrent pas les secrets cachés dans un texte libre, des structures arbitrairement imbriquées, les noms d’événements ou les piles. Le nettoyage et les listes autorisées à la source restent obligatoires, à tester avec les cas propres au module. Ne pas activer un producteur non maîtrisé en supposant que le collecteur le rendra sûr.

La collecte directe du socket Docker n’est volontairement pas activée. Son ajout ultérieur exige un accès API réellement limité aux opérations de lecture et une liste de conteneurs autorisés ; un montage `:ro` ne suffit pas. Cela évite de donner des droits sur tous les modules lors de la préparation de cette stack.

## Métriques anciennes

Les dashboards utilisent les noms canoniques du protocole. Les producteurs anciens restent visibles dans Explore mais leurs panneaux canoniques sont vides jusqu’à adaptation ou règles de normalisation vérifiées. Ne pas renommer une somme en histogramme ; ne pas mélanger plusieurs sources comptant les mêmes événements. Les mappings sont à ajouter après confirmation des manifestes et des noms réellement exposés.

## Validation

Vérifier authentification, santé, arrivée des trois signaux et corrélation sur un scénario synthétique autorisé. Passer à `connected` seulement après avoir ajouté des références de preuves dans `evidence`. `conformant-v1` exige C01–C12 applicables ; le registre ne les exécute pas et ne certifie pas automatiquement les services.
