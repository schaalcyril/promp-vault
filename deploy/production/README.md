# Déploiement GitLab CI vers K3s

Version sans BDD et sans authentification. Pas de PostgreSQL, PVC, StorageClass,
Keycloak ou Secret superadmin requis. HTTPS et l’authentification au registre restent nécessaires.
La pipeline contient directement les commandes, sans script Bash séparé.

## Agent GitLab

Contexte : `infra/kube-gitlab-agent:k3s`. Dans le dépôt propriétaire de l’agent,
`.gitlab/agents/k3s/config.yaml` autorise l’application :

```yaml
ci_access:
  projects:
    - id: infra/prompt-anonymizer
```

GitLab injecte KUBECONFIG ; ne pas le définir manuellement ni fournir un kubeconfig administrateur.
Le job sélectionne le contexte et configure la confiance TLS vers KAS.

## Préparation du cluster

1. Créer le namespace avec `deploy/production/namespace.yaml`.
2. Préparer `gitlab-registry`, Secret docker-registry avec un deploy token `read_registry` durable.
3. Préparer `prompt-vault-local-tls`, certificat/clé couvrant `prompt-vault.home.arpa`.
4. Configurer DNS et confiance TLS du navigateur, de DinD et de containerd/K3s.
5. Adapter `config/application.json` : langue, taille, règles et réseaux.

Sur ce poste, DNS application et registre pointent vers `10.254.254.1` sur l’interface persistante `lab0`, indépendante du Wi-Fi.
Le registre est `registry.gitlab.home.arpa:5005`. Les fichiers de confiance K3s sont
`/etc/rancher/k3s/registries.yaml` et `/etc/rancher/k3s/registry-ca.crt`.
Le runner utilise DinD TLS, jobs non privilégiés et privilèges réservés au service DinD.

## Pipeline

- `frontend_tests` : tests et compilation TypeScript/Vite.
- `build_images` : construit API/web, teste le backend hors réseau, valide le JSON et publie les images SHA sur la branche principale.
- `deploy_local_k3s` : job manuel sur la branche principale protégée. Génère les ConfigMaps,
  valide les manifests côté serveur, applique puis attend les deux Deployments et applique l’Ingress.

| Variable | Valeur par défaut |
|---|---|
| APP_HOST | prompt-vault.home.arpa |
| TLS_SECRET | prompt-vault-local-tls |
| INGRESS_CLASS | traefik |
| KUBE_CONTEXT | infra/kube-gitlab-agent:k3s |
| KAS_CA_CERTIFICATE | config/certificates/gitlab-local.crt |

CI_REGISTRY_IMAGE, CI_COMMIT_SHA et CI_PIPELINE_ID proviennent de GitLab.
La CA KAS n’est pas la CA du registre : ces chaînes de confiance restent distinctes.

## Manifests

- `configmaps.yaml` : nginx, proxy API et politique CSP limitée à la même origine.
- `workloads.yaml` : API/web, Services, volumes temporaires et configuration en lecture seule.
- `ingress.yaml` : HTTPS Traefik.
- La CI crée `prompt-vault-config` depuis `config/application.json`.

La configuration est chargée au démarrage, pas au build. L’annotation CI_PIPELINE_ID
provoque le remplacement des pods lors d’un redéploiement. Pas de rechargement à chaud.
L’API expose `/api/health`, `/api/config`, `/api/rules`, `/api/analyze` et `/api/analyze-stream`
sans connexion. Le catalogue public ne révèle pas les termes ou expressions personnalisés.

## Migration et vérification

Déployer ensemble les nouvelles images et le JSON sans champs OIDC. Les anciens
Secrets `prompt-vault-superadmin` et ConfigMap `prompt-vault-oidc-ca` ne sont plus montés.
La pipeline ne supprime pas automatiquement les anciennes ressources ni les ressources du projet Keycloak indépendant (`infra/keycloak`). Ne pas retirer `prompt-vault-local-tls` ni `gitlab-registry`.

Après le job, vérifier l’ouverture directe de l’application, la page Règles actives,
l’analyse d’un exemple et la restauration. `/api/health` doit indiquer `authentication: false`.
Un seul réplica API ; au maximum une analyse simultanée par processus. La limite
fonctionnelle est 10 Mio UTF-8, le proxy autorise 61 Mio pour l’encodage JSON.
