# Déploiement GitLab/Kubernetes sans BDD

La pipeline `.gitlab-ci.yml` contient directement les commandes, sans script shell
séparé. PostgreSQL, PVC, StorageClass et mode bootstrap ont été retirés.

## Fichiers de déploiement

- `namespace.yaml` : créer une fois le namespace prompt-vault.
- `secrets.example.yaml` : format du Secret local ; valeurs factices à remplacer.
- `configmaps.yaml` : nginx ; l’origine Keycloak est extraite par CI du fichier applicatif.
- `workloads.yaml` : un réplica API, un réplica web, Services internes, volumes en lecture seule.
- `ingress.yaml` : accès HTTPS.
- `../../config/application.json` : paramètres, règles et VLAN ; CI en crée la ConfigMap
  `prompt-vault-config`, montée dans `/etc/prompt-vault/application.json`.

## Compte local au déploiement

Générer le fichier privé interactivement sur un poste de confiance disposant de Python :

```text
python3 backend/app/credentials.py /chemin/prive/superadmin.json
```

Le fichier ne contient que le sel et le hash scrypt (n=131072, r=8, p=1, dklen=64).
Ne pas placer le mot de passe ou le fichier réel dans Git, une image ou les journaux CI.
Créer dans Rancher un Secret `prompt-vault-superadmin` avec la clé `superadmin.json`
contenant ce JSON, ou utiliser :

```text
kubectl -n prompt-vault create secret generic prompt-vault-superadmin --from-file=superadmin.json=/chemin/prive/superadmin.json
```

Le Secret est monté en lecture seule ; fsGroup 10001 permet sa lecture par l’API.
L’application refuse de démarrer si le fichier manque ou si son format est invalide.
L’utilisateur local s’appelle `superadmin`. Son accès `/secours` ne dépend pas de
Keycloak. Il n’existe plus d’installation par navigateur ou de route de changement
de mot de passe. Pour une rotation, remplacer le Secret et redémarrer le Deployment
API ; les sessions précédentes sont invalidées. Aucun mot de passe par défaut.

## Préparer le cluster

1. Créer le namespace : `kubectl apply -f deploy/production/namespace.yaml`.
2. Créer le Secret superadmin ci-dessus.
3. Créer `gitlab-registry`, Secret docker-registry avec un deploy token durable
   ayant read_registry. Ne pas utiliser le token éphémère CI_JOB_TOKEN.
4. Créer le Secret TLS du DNS de l’application.
5. Renseigner `config/application.json` : URL HTTPS du realm, client public PKCE S256,
   audience API et rôles. Dans Keycloak, autoriser la redirection et la déconnexion
   sur `https://VOTRE_DNS/` et Web Origins `https://VOTRE_DNS`.
6. Adapter les annotations Ingress au contrôleur : HTTPS obligatoire, taille 61 Mio
   pour l’encodage JSON, délai supérieur à 600 s et flux sans buffering. Taille de
   texte fonctionnelle limitée à 10 Mio.

Variables GitLab CI/CD :

| Variable | Contenu |
|---|---|
| KUBE_CONFIG | Variable protégée de type File : kubeconfig du compte de déploiement |
| APP_HOST | DNS application, sans protocole |
| INGRESS_CLASS | Classe du contrôleur Ingress |
| TLS_SECRET | Nom du Secret TLS déjà créé |

Keycloak et les règles sont définis dans le fichier versionné, pas dans des variables
CI concurrentes. CI_REGISTRY_* et CI_COMMIT_SHA sont fournis par GitLab. L’annotation
CI_PIPELINE_ID déclenche un redémarrage à chaque nouvelle pipeline déployée, même
si seule la configuration change. Un simple changement d’un fichier monté ou du
Secret n’est jamais un rechargement à chaud.

Runner build : Docker-in-Docker avec TLS, mode privilégié et `/certs/client` partagé.
Runner déploiement : accès API Kubernetes, droits limités au namespace (application
et lecture des Deployments, Services, ConfigMaps, Ingress, lecture des Secrets requis).
Protéger branche principale et environnement production. Le job de déploiement
reste manuel ; publication des images uniquement depuis la branche principale.
Les builds n’utilisent pas GitHub : Docker Hub, PyPI et npm ; déploiement : dépôts
Alpine pour kubectl, gettext et jq. Adapter la version kubectl à celle du cluster.

## Exploitation et limites

Le serveur charge un instantané après validation puis reste en lecture seule.
Toute modification passe par GitLab, revue, pipeline et déploiement. Les tests de
règles dans l’interface ne les activent pas. Une regex valide peut être trop coûteuse
sur certains textes ; les limites d’exécution restent actives et interrompent l’analyse.

Un seul réplica et un seul processus API : sessions locales et compteur de tentatives
sont en mémoire. Une reconnexion locale révoque la précédente ; expiration 30 minutes,
blocage après 5 échecs pendant 15 minutes. Redémarrer réinitialise les sessions et
le compteur. Ne pas activer HPA ou plusieurs workers sans revoir ce fonctionnement.

Sauvegarder les configurations versionnées et le Secret via le coffre d’entreprise.
Il n’y a plus de sauvegarde de BDD pour Prompt Vault. Keycloak externe conserve sa
propre politique d’exploitation. Les tables de correspondance de restauration
restent uniquement dans le navigateur ; elles disparaissent au rechargement.

## Migration d’un ancien déploiement

Exporter d’abord la configuration et le hash du compte local vers les nouveaux
formats, puis valider et déployer. Le mot de passe peut être conservé avec son sel
et son hash existants ; aucune session ancienne n’est transférée.
`kubectl apply` ne supprime pas les anciennes ressources : après validation de la
migration, retirer explicitement l’ancien StatefulSet/Service PostgreSQL, ses
NetworkPolicies/ConfigMap d’initialisation et tout ancien CronJob de sauvegarde.
Conserver les PVC et sauvegardes pour retour arrière tant que nécessaire. La
pipeline ne supprime aucune donnée ni ancien Secret automatiquement.

Aucun déploiement sur le cluster d’entreprise n’est effectué depuis ce poste.
