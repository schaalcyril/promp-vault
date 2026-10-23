# Modèles spaCy embarqués

Les fichiers wheel sont livrés avec le code : ne pas les exclure de l’archive du
projet ou du contexte Docker. Aucun téléchargement GitHub n’est effectué au build.

Versions fixées : `fr_core_news_sm==3.8.0`, `en_core_web_sm==3.8.0`, pour spaCy 3.8.
Provenance (téléchargement initial réalisé le 17 octobre 2026) :

- https://github.com/explosion/spacy-models/releases/download/fr_core_news_sm-3.8.0/fr_core_news_sm-3.8.0-py3-none-any.whl
- https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

Les licences des distributions sont conservées dans les wheels et extraites ici.
Le modèle français déclare LGPL-LR, le modèle anglais MIT. Conserver également
les informations de sources et licences des données contenues dans les modèles.

`SHA256SUMS` contient les empreintes calculées après téléchargement HTTPS ; il
permet de détecter une modification ultérieure, sans constituer une signature éditeur.
Le build vérifie ces empreintes puis installe les wheels sans réseau, sans index
et sans résolution de dépendances. `pip check` contrôle les dépendances déclarées.
Les autres dépendances sont installées via requirements.txt depuis PyPI.

Pour une mise à jour : récupérer les nouvelles wheels sur un poste autorisé,
vérifier leur provenance et leur compatibilité avec spaCy, actualiser les licences,
les empreintes et cette notice, puis reconstruire et exécuter les tests.
