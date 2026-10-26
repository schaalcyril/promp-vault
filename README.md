# Prompt Vault

Application interne de protection de textes et de restauration des réponses.
React/TypeScript et FastAPI avec Presidio/spaCy FR/EN. **Sans authentification et sans base de données** : ouverture directe de l’espace de travail, sans compte local ni Keycloak.
Toute personne ayant accès au service peut analyser un texte et consulter les règles actives.

## Configuration

- `config/application.json` : configuration de production, montée par ConfigMap.
- `config/application.local.json` : configuration utilisée par Docker Compose.
- [Guide des règles et VLAN](config/README.md).
- [Déploiement GitLab/K3s](deploy/production/README.md).

La configuration est validée et chargée au démarrage, pas intégrée à l’image au build.
Modifier le fichier, incrémenter `version`, puis redéployer. Aucun enregistrement par interface ou API.
La page « Règles actives » (`/regles`) affiche les catégories intégrées et les règles personnalisées activées ; les termes et expressions restent côté serveur.
Quatre exemples fictifs actifs sont fournis : serveurs, domaines, références de dossiers et jetons non restaurables. Les adapter ou les désactiver avant utilisation selon vos besoins.

## Installation locale

```sh
docker compose up -d --build
```

Ouvrir http://localhost:3080/. Aucun secret d’authentification ni initialisation préalable.
Compose monte directement `config/application.local.json` en lecture seule.
Les anciennes copies privées `.local/application.json` et `.local/superadmin.json` ne sont plus utilisées.

## Protection et restauration

- Analyse français/anglais automatique par passage, ou choix manuel ; repli bilingue en cas de doute.
- Détecteurs techniques et de secrets, listes de mots-clés et expressions régulières bornées.
- Maximum 10 Mio UTF-8, configurable ; progression et annulation du traitement.
- Revue des détections, exclusions, masquage manuel et bilan de restauration.
- Référentiel IPv4/VLAN avec labels anonymes, sans chevauchement des réseaux.
- Correspondances en mémoire du navigateur, perdues au rechargement. Les secrets ne sont jamais restaurés.

Aucun historique de prompts, import de fichiers ou stockage serveur des textes. L’analyse automatique peut omettre des données sensibles : vérifier le résultat avant partage.
Un seul processus API et un seul réplica prévus ; une analyse simultanée par processus, réponse 429 si occupé. Le flux s’arrête après dix minutes ou à l’annulation.
L’accès réseau à l’application détermine désormais qui peut l’utiliser. HTTPS reste configuré.

## Build et tests

Les modèles spaCy sont inclus dans `backend/vendor` avec licences et empreintes.
Aucun téléchargement GitHub au build ; Docker Hub, PyPI et npm restent nécessaires.

```sh
docker compose build api web
docker compose run --rm --no-deps api python -m pytest -q -p no:cacheprovider
npm --prefix frontend ci
npm --prefix frontend test
npm --prefix frontend run build
```

## Migration depuis la version authentifiée

Retirer de `settings` les champs issuer, internal_issuer, client_id, audience, user_role et admin_role.
Conserver default_language, max_text_mib, les règles et réseaux existants. Les champs inconnus sont refusés.
Déployer les nouvelles images avec la nouvelle configuration : les routes de connexion et d’administration sont supprimées.
La CI ne demande plus `prompt-vault-superadmin` ni `prompt-vault-oidc-ca`.
Les anciennes ressources et données du cluster ne sont pas supprimées automatiquement. Le lab Keycloak est géré séparément dans `infra/keycloak` ; ce dépôt ne contient plus ses manifests ni son realm.
