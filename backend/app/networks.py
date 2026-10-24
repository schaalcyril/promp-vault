"""Global VLAN catalogue; only anonymous grouping labels leave analysis."""
import ipaddress
from pydantic import BaseModel,ConfigDict,Field,model_validator
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
def catalogue():
    from .configuration import current
    config=current()
    return [{'id':i,'version':config['version'],'definition':row} for i,row in enumerate(config['networks'],1)]

def snapshot():
    result=[]
    for group,row in enumerate(catalogue(),1):
        if row['definition']['enabled']:
            for subnet,cidr in enumerate(row['definition']['cidrs'],1):
                result.append((ipaddress.ip_network(cidr),f'VLAN_{group}_RESEAU_{subnet}'))
    return result
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
