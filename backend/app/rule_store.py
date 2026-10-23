"""Read-only access to deployment rules. No database or write operation."""
from fastapi import HTTPException
from .configuration import current

def list_rules():
    config=current()
    return [{'id':i,'version':config['version'],**rule} for i,rule in enumerate(config['rules'],1)]

def active_rules():return [row['definition'] for row in list_rules() if row['enabled']]

def get(rule_id):
    for row in list_rules():
        if row['id']==rule_id:return row
    raise HTTPException(404,'Règle introuvable')
