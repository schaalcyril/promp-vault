"""Global VLAN catalogue; only anonymous grouping labels leave analysis."""
import ipaddress
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .auth import administrator
router=APIRouter(prefix='/api/admin/networks',dependencies=[Depends(administrator)])
class Definition(BaseModel):
    model_config=ConfigDict(extra='forbid')
    name:str=Field(min_length=1,max_length=100)
    vlan:int|None=Field(default=None,ge=1,le=4094)
    cidrs:list[str]=Field(min_length=1,max_length=100)
    enabled:bool=False
    @model_validator(mode='after')
    def validate_networks(self):
        self.name=self.name.strip()
        if not self.name:raise ValueError('Nom requis')
        parsed=[]
        for cidr in self.cidrs:
            if '/' not in cidr:raise ValueError('CIDR requis')
            network=ipaddress.ip_network(cidr,strict=True)
            if network.version!=4:raise ValueError('IPv4 uniquement pour ce jalon')
            if any(network.overlaps(other) for other in parsed):raise ValueError('Sous-réseaux en chevauchement')
            parsed.append(network)
        self.cidrs=[str(network) for network in parsed]
        return self
class Sample(BaseModel):
    model_config=ConfigDict(extra='forbid')
    address:str=Field(min_length=1,max_length=45)

def catalogue():
    from .configuration import current
    config=current()
    return [{'id':i,'version':config['version'],'definition':row} for i,row in enumerate(config['networks'],1)]

@router.get('')
def listing():return catalogue()

def snapshot():
    result=[]
    for group,row in enumerate(catalogue(),1):
        if row['definition']['enabled']:
            for subnet,cidr in enumerate(row['definition']['cidrs'],1):
                result.append((ipaddress.ip_network(cidr),f'VLAN_{group}_RESEAU_{subnet}'))
    return result
@router.post('/test')
def test_address(data:Sample):
    try:address=ipaddress.ip_address(data.address.strip())
    except ValueError:raise HTTPException(422,'Adresse IP non valide') from None
    matches=[]
    for row in catalogue():
        if row['definition']['enabled']:
            for cidr in row['definition']['cidrs']:
                if address in ipaddress.ip_network(cidr):matches.append({'name':row['definition']['name'],'vlan':row['definition']['vlan'],'cidr':cidr})
    return {'matches':matches}
def annotate(text,hits,networks):
    for hit in hits:
        if hit['category']!='IP' or hit.get('secret'):continue
        value=text[hit['start']:hit['end']]
        try:address=ipaddress.ip_address(value)
        except ValueError:continue
        for network,label in networks:
            if address in network:
                hit['network_label']=label
                break
    return hits
