"""Read-only rule snapshot and public catalogue without matching values."""
from .configuration import current

def active_rules():
    return [row['definition'] for row in current()['rules'] if row['enabled']]

def public_catalogue():
    from .engine import RULES, STRUCTURED_MAP, NLP_MAP, SECRET_TYPES
    labels={'PERSON':'Personnes','LOCATION':'Lieux','PHONE':'Téléphones','EMAIL':'Adresses e-mail',
        'IBAN':'IBAN','CARD':'Cartes bancaires','PASSWORD':'Mots de passe','TOKEN':'Jetons et clés API',
        'PRIVATE_KEY':'Clés privées','SECRET':'Secrets détectés','IP':'Adresses et réseaux IP',
        'FQDN':'Noms de domaine','HOSTNAME':'Noms de serveurs','MAC':'Adresses MAC',
        'USERNAME':'Identifiants','US_SSN':'Numéros de sécurité sociale américains',
        'ADDRESS':'Adresses postales anglaises','ORGANIZATION':'Organisations (formats anglais)'}
    categories=set(STRUCTURED_MAP.values())|set(NLP_MAP.values())|{r[0] for r in RULES}|SECRET_TYPES|{'IP','FQDN'}
    config=current()
    return {'version':config['version'],
        'builtin':[{'name':labels.get(c,c),'category':c,'secret':c in SECRET_TYPES} for c in sorted(categories)],
        'custom':[{'name':r['definition']['name'],'category':r['definition']['category'],
                   'kind':r['definition']['kind'],'secret':r['definition']['secret']}
                  for r in config['rules'] if r['enabled']]}
