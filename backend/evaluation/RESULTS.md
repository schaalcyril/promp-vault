# Prompt Vault — corrections du moteur

## Résultat sur le même corpus synthétique

| Mesure | Avant | Après |
|---|---:|---:|
| Entités exactes (limites et catégorie) | 11/32 | 32/32 |
| Entités entièrement couvertes | 21/32 | 32/32 |
| Précision | 34,38 % | 100 % |
| Rappel | 34,38 % | 100 % |
| F1 | 34,38 % | 100 % |

30 scénarios de développement, utilisés pour diagnostiquer et corriger les défauts. Ces pourcentages ne sont pas une estimation de performance sur des données réelles ou sur un jeu aveugle.

## Changements

- Validation des IPv4/IPv6 complètes, CIDR et zones IPv6 ; conservation de la ponctuation extérieure.
- Détection MAC explicite, indépendante de la langue.
- Extraction des valeurs secrètes JSON/YAML entre guillemets, y compris espaces et échappements ; éléments XML traités lexicalement sans parseur externe.
- Séparation des utilisateurs, mots de passe et domaines dans les URL authentifiées.
- Priorité aux catégories précises sur SECRET ; priorité des formats établis sur les détections NLP chevauchantes.
- Règles de compte utilisateur resserrées et détection de paires avec un libellé explicite « credentials » ou « identifiants ».
- Reconnaissance contextuelle des noms d’organisation après un libellé client/entreprise.
- Exclusion des noms de fichiers seulement dans un contexte de fichier explicite, sans liste blanche globale des domaines portant ces suffixes.
- Reconnaissance structurée Presidio utilisant les registrations disponibles également pour les textes français.
- Verrou autour des paramètres globaux de detect-secrets pour éviter les interférences entre analyses concurrentes.

## Validation

27 tests backend et 2 tests frontend réussis. Les variantes ajoutées couvrent notamment IPv6, secrets avec espaces/échappements, XML, URL, ponctuation, noms de fichiers, frontières de blocs NLP et invariants de non-restauration. Tests backend et corpus exécutés sans réseau.

Backend reconstruit et redémarré. Vérification HTTP réelle via localhost:3080 : IPv6 et secret XML correctement extraits ; package.json non masqué dans le contexte testé.

Pic RSS du processus d’évaluation : 322.7 Mio. Latence médiane des courts scénarios, modèles préchargés : 17.02 ms ; maximum 84.32 ms. Ces durées ne comprennent pas le navigateur ni le réseau HTTP.

## Limites restantes

- Corpus réduit, connu pendant les corrections ; validation indépendante à organiser.
- Noms de clients non explicitement contextualisés et secrets arbitraires sans format : aucune garantie de détection.
- Règles lexicales non équivalentes à un parseur complet JSON/YAML/XML ; contenus encodés, structures atypiques et cas malformés nécessitent davantage de tests.
- Un chevauchement de secrets réellement ambigu reste masqué sur toute son étendue par précaution.
- La cible de 10 Mio, la progression et l’annulation réelle côté serveur restent à valider/implémenter.
- Note historique : la version actuelle ne nécessite plus Keycloak, PostgreSQL ni interface d’administration.
