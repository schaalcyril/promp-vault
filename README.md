# Prompt Vault

Application interne de protection de textes et de restauration des réponses.
React/TypeScript et API FastAPI avec Presidio/spaCy FR/EN. **L’application n’utilise
aucune base de données** : paramètres Keycloak, règles et VLAN sont validés et
chargés depuis un fichier JSON au démarrage. Le compte local reçoit un hash scrypt
via un fichier secret distinct.

## Configuration versionnée

- [config/application.json](config/application.json) : configuration de déploiement.
- [config/application.local.json](config/application.local.json) : exemple pour le poste local.
- [Guide des règles et VLAN](config/README.md).
- [Déploiement GitLab/Kubernetes](deploy/production/README.md).

Une erreur de JSON, règle, URL, réseau ou secret empêche le démarrage. Les fichiers
sont lus une seule fois par processus : une modification exige un redémarrage ou
un redéploiement. L’interface ne peut pas les écrire. Les règles actives sont communes
à tous les utilisateurs ; les tests de règles ne changent pas leur activation.

## Installation locale neuve

Depuis la racine du projet :

```sh
python3 scripts/setup-keycloak.py
cp config/application.local.json .local/application.json
python3 backend/app/credentials.py .local/superadmin.json
chmod 700 .local
chmod 444 .local/application.json .local/superadmin.json
docker compose up -d --build
```

Le générateur demande et confirme le mot de passe sans l’afficher ni le passer en
argument. Il crée uniquement le sel et le hash, en refusant d’écraser un fichier
existant. Les fichiers montés sont lisibles par l’utilisateur du conteneur ; leur
répertoire parent `.local` reste privé (0700) sur le poste. Ne pas appliquer ces
commandes de copie à une installation migrée : conserver ses fichiers existants.

Interface : http://localhost:3080/ ; compte local `superadmin` :
http://localhost:3080/secours. Il n’existe plus d’écran d’installation initiale ni
de changement de mot de passe dans l’application. Pour une rotation, générer un
nouveau fichier privé, le remplacer au déploiement et redémarrer l’API.

Le Keycloak de démonstration garde son propre volume `keycloak-data` : c’est une
dépendance de développement distincte de Prompt Vault. En entreprise, utiliser
l’instance Keycloak existante. Les comptes de test sont documentés dans le fichier
privé `.local/ACCES.md` ; ne pas les reprendre en production.

## Droits et sessions

| Compte | Accès |
|---|---|
| Utilisateur Keycloak | Analyse et restauration |
| Administrateur Keycloak | Analyse, restauration, consultation et test des règles/VLAN |
| Superadmin local | Même accès, plus consultation système et test de connexion Keycloak |

Aucun rôle ne peut enregistrer une règle, un VLAN, une configuration ou un mot de
passe depuis l’interface/API. Modifier GitLab puis redéployer.

L’authentification Keycloak utilise Authorization Code avec PKCE S256 ; les JWT
sont contrôlés côté API (signature, émetteur, audience, expiration, client et rôles).
Le compte local fonctionne sans Keycloak. Une seule session locale à la fois,
30 minutes maximum, révocation à la déconnexion et au redémarrage. Le serveur ne
conserve que le hash du jeton. Cinq tentatives incorrectes bloquent la connexion
pendant 15 minutes ; le compteur est en mémoire et repart à zéro au redémarrage.
**Un seul processus API et un seul réplica sont supportés** pour ces sessions et
cette limitation. Ne pas ajouter de workers Uvicorn ou de HPA sans revoir ce mécanisme.

## Protection et restauration

- Détection automatique FR/EN par passage, ou choix manuel ; repli bilingue en cas
  de doute. Les détecteurs techniques et de secrets restent actifs dans les deux cas.
- Textes limités à 10 Mio UTF-8 au maximum, réglable dans la configuration.
- Progression, annulation, revue des détections par pages de 50, exclusions et
  masquage manuel. Une analyse simultanée par processus pour le flux.
- Règles personnalisées : listes de termes ou expressions régulières bornées.
- Référentiel IPv4/VLAN : préserve les groupes réseau via des labels anonymes.
  Pas de chevauchement de CIDR ni de déduction automatique de topologie.
- Bilan de restauration : occurrences restaurées, secrets maintenus masqués,
  marqueurs inconnus ou potentiellement altérés. Aucune restauration devinée.

Les correspondances restent en mémoire du navigateur et sont perdues au
rechargement. Les secrets ne sont jamais restaurés. Aucun historique de prompts,
import de fichiers, export de correspondances ni stockage serveur des textes.
Les fichiers de règles peuvent contenir des noms internes : protéger l’accès à GitLab
et aux ConfigMaps. L’analyse automatique peut omettre des données sensibles ; revoir
le résultat avant partage. Les benchmarks synthétiques de `backend/evaluation`
ne constituent pas une garantie de qualité ou de performance en production.

## Build et vérification

Les modèles spaCy FR/EN sont inclus dans [backend/vendor](backend/vendor/README.md),
avec licences et empreintes vérifiées au build. Aucun téléchargement GitHub :
Docker Hub, PyPI et npm restent nécessaires. Le thème ne charge aucune ressource distante.

```sh
docker compose build api web
docker compose run --rm --no-deps api python -m pytest -q -p no:cacheprovider
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build
```

Les tests backend utilisent des fichiers temporaires et des secrets synthétiques,
sans BDD ni connexion Keycloak. `scripts/check-oidc.py` vérifie les comptes Keycloak
locaux contre les services démarrés. `scripts/check-recovery.py` demande le mot de
passe interactivement pour vérifier l’accès local et sa révocation.

## Migration de l’ancien stockage

Sur ce poste, la configuration et le hash existants ont été exportés dans les
fichiers privés `.local/application.json` et `.local/superadmin.json`. Le mot de passe
local reste le même. L’ancien conteneur PostgreSQL est arrêté et son volume conservé
pour retour arrière ; aucune donnée de cette ancienne base n’a été supprimée.

Pour un autre environnement déjà installé, exporter paramètres, règles, réseaux,
sel et hash avant migration. Les règles deviennent des entrées `enabled/definition`,
les réseaux des définitions simples ; le secret contient seulement `salt/hash`.
Valider l’export avant d’arrêter l’ancien service. La nouvelle version n’effectue
aucune migration automatique au démarrage et ne lit plus DATABASE_URL.
