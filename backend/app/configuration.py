"""Validate a deployment snapshot once; never reload configuration during requests."""
import argparse
import copy
import ipaddress
import json
import os
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, model_validator, ValidationError
from .custom_rules import RuleDefinition
from .system_settings import Settings
from .networks import Definition

class Rule(BaseModel):
    model_config=ConfigDict(extra='forbid')
    enabled: bool = False
    definition: RuleDefinition

class Configuration(BaseModel):
    model_config=ConfigDict(extra='forbid')
    version: int = Field(ge=1)
    settings: Settings
    rules: list[Rule] = Field(max_length=100)
    networks: list[Definition] = Field(max_length=100)

    @model_validator(mode='after')
    def unique(self):
        names=[r.definition.name.casefold() for r in self.rules]
        if len(names)!=len(set(names)):raise ValueError('Noms de règles en doublon')
        vlans=set();subnets=[]
        for row in self.networks:
            if row.vlan is not None:
                if row.vlan in vlans:raise ValueError('Numéro VLAN en doublon')
                vlans.add(row.vlan)
            for cidr in row.cidrs:
                net=ipaddress.ip_network(cidr)
                if any(net.overlaps(other) for other in subnets):raise ValueError('Chevauchement de réseaux')
                subnets.append(net)
        return self

_snapshot=None

def unique_keys(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('Clé JSON en doublon')
        result[key]=value
    return result

def read(path):
    try:
        with Path(path).open('rb') as f:data=f.read(900*1024+1)
        if len(data)>900*1024:raise ValueError()
        raw=json.loads(data,object_pairs_hook=unique_keys)
        return Configuration.model_validate(raw).model_dump()
    except (OSError,ValueError,ValidationError,RecursionError):
        # Pydantic errors can echo internal names or values: keep them out of logs.
        raise RuntimeError('Configuration de déploiement absente ou invalide : vérifier le fichier JSON, les règles et les réseaux.') from None

def initialize():
    global _snapshot
    _snapshot=read(os.environ.get('APP_CONFIG_FILE','/etc/prompt-vault/application.json'))

def current():
    if _snapshot is None:raise RuntimeError('Configuration non initialisée')
    return copy.deepcopy(_snapshot)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Valider une configuration sans lancer le serveur.')
    parser.add_argument('file');args=parser.parse_args()
    read(args.file)
    print('Configuration valide.')
