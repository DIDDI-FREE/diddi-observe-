# Déploiement différé

Aucune écriture Portainer n’a été réalisée pour créer ce dépôt. Le plan de déploiement devra confirmer le domaine, le périmètre de tous les conteneurs DiddiObserve, le réseau, les volumes et les secrets. L’autorisation précédente limitée au seul conteneur diddi-observe ne s’étend pas implicitement aux autres modules.

## Profil local avec bind mounts

1. Cloner le dépôt sur l’hôte qui exécutera Docker. Ne pas inclure `audit-sources` ou un inventaire privé.
2. Installer un certificat TLS délivré pour le domaine réel dans `secrets/tls.crt` et `secrets/tls.key`. Installer un mot de passe administrateur aléatoire dans `secrets/grafana_admin`.
3. Copier `.env.example` vers `.env`. Définir `GRAFANA_ROOT_URL` et l’adresse d’écoute voulue. Le défaut loopback évite une publication involontaire.
4. Définir les droits : dossier secrets accessible au seul opérateur ; fichiers montés individuellement lisibles par les UID du conteneur correspondant. Le bootstrap local utilise dossier 0700 et fichiers partagés 0644 pour les montages individuels. Ne pas exposer le répertoire secrets à un serveur HTTP.
5. Générer les configurations. Réserver et surveiller le stockage. Sauvegarder la configuration et les secrets via des canaux distincts.
6. Vérifier `docker compose config`, les validateurs natifs et les tests. Utiliser un nom de projet distinct de la démonstration.

## Portainer

Utiliser **`compose.portainer.yaml`** : les images sont construites depuis Git avec leurs configurations intégrées. Aucun checkout manuel sur l’hôte ni bind mount de configuration n’est nécessaire. Voir [PORTAINER.md](PORTAINER.md) pour les variables, TLS et mises à jour. Le fichier `compose.yaml` reste réservé au profil local décrit ci-dessus.

Fournir les secrets via les variables Portainer, jamais dans Git ni dans des arguments de build. Aucun déploiement distant n’est exécuté par la publication de ce correctif.

## Réseau

`backend` est interne. Pour joindre un service existant, ajouter **uniquement aux collecteurs nécessaires** le réseau de collecte autorisé ou une route privée. Ne pas modifier les réseaux des applications sans autorisation. Un service HTTP peut être collecté seulement si le registre déclare explicitement l’isolation du réseau ; utiliser HTTPS vérifié dans les autres cas.

Les URLs du registre ne sont pas saisies par des utilisateurs non fiables : elles déterminent des connexions sortantes. Revue obligatoire des destinations, absence de credentials dans l’URL, pare-feu sortant et autorisation du réseau cible. Le blackbox exporter reste interne et n’est jamais publié.

## Stockage et rétention

Le profil livré est staging : Loki 14 jours, métriques 30 jours avec plafond Prometheus de 10 Go, traces 7 jours. Le plafond taille peut réduire la durée disponible de Prometheus. Les données sont dans cinq volumes nommés. Le stockage local de Tempo est destiné au pilote ; prévoir un stockage objet pour la production et valider la migration avec la version sélectionnée.

Évaluer les débits pendant le pilote, définir des quotas et alertes disque sur l’hôte avant ouverture générale. Les plafonds RAM Compose ne remplacent pas un dimensionnement. Les logs Docker sont bornés à cinq fichiers de 10 MiB par conteneur central.

## Identités et accès

Créer les utilisateurs Grafana avec les rôles Viewer/Editor appropriés et réserver Admin à l’exploitation. Tous les utilisateurs d’une même organisation Grafana peuvent potentiellement accéder aux sources de données autorisées à cette organisation ; les dossiers de dashboards ne constituent pas une séparation des données. Utiliser des instances/organisations et une architecture de sources adaptée si plusieurs équipes doivent être isolées. Ne pas ouvrir une instance commune production/staging à des utilisateurs dont les droits divergent.

Les notifications restent locales jusqu’au choix du canal et de ses destinataires. Le récepteur local ne conserve que la trace de réception ; ce n’est pas une archive d’incidents.
