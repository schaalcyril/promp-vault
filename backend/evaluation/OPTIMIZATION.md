# Prompt Vault — optimisation du moteur

## Mesures

| Entrée | Avant | Après | Pic RSS après |
|---|---:|---:|---:|
| 1 Mio de logs répétitifs | 62,32 s | 31,56 s | 369,3 Mio |
| 10 Mio de logs répétitifs | Non terminé à 300 s | 57,67 s | 379,5 Mio |
| 1 Mio de logs variés | Non mesuré sur ce profil | 46,09 s | 377,5 Mio |

Mesures isolées du moteur, modèles préchargés, conteneur sans réseau limité à 4 Gio, sur le même poste Ubuntu i7-6820HQ. Une exécution par cas : ce ne sont pas des percentiles ni un engagement de latence. Les caches de résultats commencent vides pour chaque requête. Le test varié change les identifiants d’événement et les durées ; le profil répétitif conserve des lignes identiques. Le poste peut exécuter d’autres tâches : les mesures restent indicatives.

Le facteur d’amélioration est d’environ 1,97 sur le test répétitif de 1 Mio. Le temps exact avant optimisation à 10 Mio est inconnu : il dépassait le délai de 300 secondes. Ne pas présenter 300 secondes comme une durée d’analyse terminée.

## Modifications

1. Un seul passage spaCy par bloc ; ses résultats linguistiques sont fournis aux reconnaisseurs structurés et aux reconnaisseurs NLP. Le contexte linguistique est celui de la langue sélectionnée.
2. Réutilisation des détections de secrets sur une ligne strictement identique, limitée à 512 lignes de 4 096 caractères maximum.
3. Réutilisation des résultats sur les blocs strictement identiques, limitée à 128 blocs de 20 000 caractères.
4. Décalage des positions à chaque occurrence, sans dédupliquer les occurrences dans le texte.

Ces caches vivent uniquement pendant la requête. Ils ne sont pas globaux, ne persistent pas sur disque et ne sont pas partagés entre utilisateurs. Les clés contiennent temporairement du texte sensible en mémoire, comme le texte déjà analysé ; il ne faut pas les exporter vers un cache applicatif partagé. Aucun détecteur n’a été supprimé et les logs ne sont pas exclus du NLP.

## Validation

- Les 31 tests backend existants passent ; 2 nouveaux tests vérifient les positions de 700 secrets répétés et l’absence de réutilisation du cache entre requêtes : 33 tests backend au total.
- Les tests frontend n’ont pas été rejoués : aucun code frontend modifié dans ce jalon.
- Le corpus annoté de 30 scénarios conserve 32/32 détections exactes.
- Comparaison avant/après sur quatre jeux générés supplémentaires : 1 643 détections comparées, sans ajout ni disparition, avec positions, catégories et indicateur secret inchangés. Ces jeux contiennent du français, de l’anglais, des logs variés et des frontières de blocs.

Ces validations ne démontrent pas l’équivalence sur tous les textes : en particulier, partager les résultats linguistiques peut modifier les scores contextuels de certains formats. Un corpus indépendant plus large reste nécessaire.

## Limites et suite

Le test moteur de 10 Mio répétitifs termine désormais. Cela ne valide pas un délai inférieur à une minute pour tous les textes de 10 Mio. Le profil varié n’a été mesuré qu’à 1 Mio ; le parcours complet navigateur/réseau/rendu à 10 Mio reste à mesurer. La détection linguistique demeure coûteuse sur les contenus uniques.

Les mesures de charge ne sont pas un corpus de précision : les 485 détections produites sur les logs variés ne sont pas toutes annotées ni validées. Elles doivent être examinées pour identifier les faux positifs sur les identifiants numériques avant d’étendre le pilote.

Priorités : corpus indépendant plus représentatif, évaluation des faux positifs numériques, puis performances de bout en bout sur des contenus variés. Keycloak et administration restent des jalons distincts.
