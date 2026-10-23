# Configuration chargée au démarrage

`application.json` est le fichier de production, monté par une ConfigMap. Les exemples
ne contiennent pas de règles d’entreprise. Modifier le fichier, incrémenter `version`,
faire valider le changement puis redéployer. Aucun rechargement à chaud.

- `settings` : realm Keycloak HTTPS, client, audience, noms des rôles, langue et
  taille maximale. `internal_issuer` est facultatif et désigne l’URL du même realm
  joignable depuis l’API. Seul le Compose local autorise HTTP.
- `rules` : jusqu’à 100 règles, actives si `enabled` vaut true. Toutes les règles,
  même désactivées, doivent être syntaxiquement valides ; les noms sont uniques.
- `networks` : jusqu’à 100 groupes de 100 CIDR IPv4. Aucun chevauchement, même entre
  groupes inactifs. Numéro VLAN facultatif, unique, entre 1 et 4094.

Exemple d’entrée dans `rules` :

```json
{
  "enabled": true,
  "definition": {
    "name": "Serveurs internes",
    "kind": "list",
    "category": "SERVER",
    "secret": false,
    "case_sensitive": false,
    "terms": ["srv-exemple-01", "exemple.interne"]
  }
}
```

Pour une expression régulière, utiliser `kind: "regex"` et le champ `pattern`.
Les listes sont limitées à 200 termes, 200 caractères par terme et 20 000 au total ;
les regex à 1 000 caractères. Le matching impose une durée et un nombre de résultats
maximum. Les catégories PASSWORD, TOKEN, PRIVATE_KEY et SECRET sont toujours
non restaurables, même si `secret` est false. La validation syntaxique n’assure pas
la pertinence d’une règle : tester aussi des contre-exemples avant son activation.

Exemple d’entrée dans `networks` :

```json
{"name":"Production","vlan":120,"cidrs":["10.20.1.0/24"],"enabled":true}
```

Le fichier complet est limité à 900 Kio pour son transport dans une ConfigMap Kubernetes. Les clés JSON dupliquées et les champs
inconnus sont refusés. L’API n’expose au navigateur utilisateur que les paramètres
publics nécessaires à la connexion et à l’analyse. Le superadmin peut consulter
les paramètres système ; les administrateurs peuvent consulter et tester règles/VLAN.

Validation sans lancer le serveur :

```text
python -m app.configuration /chemin/application.json
```

Cette commande s’exécute dans l’image API ; elle ne lit pas de mot de passe et ne
contacte pas Keycloak. La pipeline l’exécute sur le fichier versionné avant publication.
