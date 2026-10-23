# Keycloak de test sur K3s local

Cette instance accompagne Prompt Vault sur le poste, indépendamment du déploiement
applicatif de la pipeline. Elle ne convient pas à une exploitation en production.

- Namespace : `prompt-vault`.
- Console : `https://prompt-vault.home.arpa/auth/admin/`.
- Issuer : `https://prompt-vault.home.arpa/auth/realms/prompt-vault`.
- Client public : `prompt-vault-web`, code d’autorisation avec PKCE S256.
- Audience : `prompt-vault-api` ; rôles : `user` et `admin`.
- Comptes de test : `utilisateur` et `administrateur` ; console : `keycloak-admin`.

## Fichiers et secrets

`keycloak.yaml` contient le Service, Deployment et Ingress Traefik HTTPS.
`realm.json` contient le realm et des références aux variables d’environnement des
mots de passe. Il ne contient aucun mot de passe réel.

Les valeurs privées générées sur le poste sont dans `.local/k3s/keycloak.env`
(mode 0600) et le récapitulatif `.local/k3s/ACCES.md` (mode 0600). Elles sont
exclues de Git. Le Secret `keycloak-local-credentials` contient les clés
`KC_BOOTSTRAP_ADMIN_PASSWORD`, `TEST_USER_PASSWORD` et `TEST_ADMIN_PASSWORD`.
Ne pas afficher ces valeurs dans les logs ou les placer dans la CI.

Le certificat applicatif est signé par une CA locale de test. Le Secret TLS
`prompt-vault-local-tls` contient le certificat et la clé. Le certificat public de
la CA est `.local/k3s/ca.crt` ; importer uniquement ce fichier comme autorité de
confiance dans le navigateur. Les fichiers `ca.key` et `tls.key` restent privés.
Le certificat serveur expire après 90 jours et la CA après 365 jours.

Sur le poste, ajouter la résolution `192.168.1.63 prompt-vault.home.arpa`
(par exemple dans `/etc/hosts`). Le cluster utilise une entrée dédiée dans
`kube-system/coredns-custom`. L’adresse du poste doit rester stable.

## Reprise du déploiement

Après création du namespace, des Secrets et de la ConfigMap du realm :

```sh
kubectl -n prompt-vault create configmap keycloak-local-realm \
  --from-file=realm.json=deploy/local-k3s/realm.json --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f deploy/local-k3s/keycloak.yaml
kubectl -n prompt-vault rollout status deployment/keycloak-local
```

Les Secrets ont été créés séparément depuis les fichiers privés du poste.
Ils ne sont pas recréés par ce manifeste et ne sont pas inclus dans Git.

## Persistance et intégration

La base embarquée est dans un `emptyDir` : le remplacement du pod efface les
modifications effectuées dans la console et réimporte `realm.json`. Les comptes
retrouvent alors les mots de passe conservés dans le Secret. Le mode `Recreate`
assure qu’un seul pod utilise cette configuration de test.

Après modification du realm ou des Secrets, redémarrer `deployment/keycloak-local`.
Ne pas utiliser cette procédure avec une instance contenant des données à conserver.

Le déploiement de Prompt Vault reste distinct : configurer son issuer ci-dessus et
la confiance envers cette CA pour ses accès OIDC HTTPS, puis vérifier le login
complet après déploiement de l’application. Ne pas désactiver la vérification TLS.
