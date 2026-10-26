# Infrastructure K3s locale

Prompt Vault ne nécessite ni authentification utilisateur ni base de données.
Les manifests applicatifs et la procédure CI sont décrits dans [le guide de production](../production/README.md).

Ce dossier conserve uniquement les exemples et certificats publics nécessaires à l’infrastructure :

- `agent-ci-access.example.yaml` : autorisation du projet auprès de l’agent GitLab.
- `registries.example.yaml` : confiance TLS du registre pour containerd/K3s.
- `registry-ca.crt` : certificat public du registre local ; à adapter à votre environnement.

Le lab nomade utilise `10.254.254.1` sur l’interface persistante `lab0`, indépendamment du Wi-Fi.
Les noms GitLab, registre et application doivent résoudre depuis le poste et les jobs/pods.
Ne pas désactiver la vérification TLS ni publier les clés privées.

Le lab Keycloak est géré séparément dans le projet `infra/keycloak` ; aucun de ses composants ne doit être déployé depuis Prompt Vault.
