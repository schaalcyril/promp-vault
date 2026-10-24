# Configuration chargée au démarrage

`application.json` est le fichier de production, monté par une ConfigMap. Les exemples
ne contiennent pas de règles d’entreprise. Modifier le fichier, incrémenter `version`,
faire valider le changement puis redéployer. Aucun rechargement à chaud.

- `settings` : `default_language` (auto, fr ou en) et `max_text_mib` (1 à 10). Aucun paramètre d’authentification.
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
publics nécessaires à l’analyse. La page `/regles` expose les noms, catégories, types
et le caractère restaurable des règles actives, sans leurs termes ni expressions.
Ne pas mettre de secret dans le nom d’une règle, puisqu’il est visible par tous.

## Exemples fournis dans les fichiers JSON

Les quatre règles d’exemple sont actives, utilisent uniquement des valeurs fictives et
peuvent être désactivées avec `enabled: false` :

| Exemple | Texte détecté | Restauration |
|---|---|---|
| Serveurs | `atlas-demo-01`, `orion-demo-02` | Oui |
| Domaines | `intranet.example.test`, `api.example.test` | Oui |
| Référence de dossier | `DOS-DEMO-123456` | Oui |
| Jeton fictif | `PV-DEMO-SECRET-ABCDEF123456` | Non |

Les regex utilisent des doubles antislashs dans le JSON (par exemple `\\b` pour une
limite de mot). Le fichier local et celui de production sont indépendants.
Une règle personnalisée désactivée disparaît du catalogue ; les détecteurs intégrés
restent actifs et peuvent détecter le même texte (par exemple un domaine).

Validation sans lancer le serveur :

```text
python -m app.configuration /chemin/application.json
```

Cette commande s’exécute dans l’image API ; elle ne lit pas de mot de passe et ne
effectue aucun accès réseau. La pipeline l’exécute sur le fichier versionné avant publication.
