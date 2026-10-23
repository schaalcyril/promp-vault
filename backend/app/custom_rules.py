"""Bounded matching of administrator rules. Samples and matches are never stored."""
import time
from typing import Literal
import regex
from pydantic import BaseModel, Field, ConfigDict, model_validator

SECRET_CATEGORIES = {'PASSWORD', 'TOKEN', 'PRIVATE_KEY', 'SECRET'}

class RuleDefinition(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=100)
    kind: Literal['list', 'regex'] = 'list'
    category: str = Field(default='CUSTOM', pattern=r'^[A-Z][A-Z0-9_]{0,31}$')
    secret: bool = True
    case_sensitive: bool = False
    pattern: str = Field(default='', max_length=1000)
    terms: list[str] = Field(default_factory=list, max_length=200)

    @model_validator(mode='after')
    def validate_definition(self):
        self.name=self.name.strip()
        if not self.name:
            raise ValueError('Nom requis')
        if self.category in SECRET_CATEGORIES:
            self.secret = True
        if self.kind == 'list':
            self.terms = list(dict.fromkeys(term.strip() for term in self.terms if term.strip()))
            if not self.terms or any(not term or len(term)>200 for term in self.terms) or sum(map(len,self.terms))>20000:
                raise ValueError('Liste non valide')
            self.pattern = ''
        else:
            self.terms = []
            if not self.pattern:
                raise ValueError('Expression requise')
        try:
            compiled = compile_rule(self.model_dump())
            if compiled.search('', timeout=0.1):
                raise ValueError('Correspondance vide interdite')
        except (regex.error, TimeoutError, RecursionError, OverflowError):
            raise ValueError('Expression non valide') from None
        return self

class RuleExecutionError(Exception):
    pass

def compile_rule(rule):
    # Lists match entire words/phrases, never a substring inside another word.
    source = rule['pattern'] if rule['kind']=='regex' else r'(?<!\w)(?:'+ '|'.join(regex.escape(t) for t in sorted(rule['terms'], key=len, reverse=True)) +r')(?!\w)'
    return regex.compile(source, regex.VERSION1 | (0 if rule['case_sensitive'] else regex.IGNORECASE))

def match_rules(text, rules, budget=2.0, max_hits=100000):
    deadline = time.monotonic()+budget
    hits=[]
    try:
        for rule in rules:
            remaining=deadline-time.monotonic()
            if remaining<=0:
                raise TimeoutError()
            compiled=compile_rule(rule)
            for match in compiled.finditer(text, timeout=remaining):
                if time.monotonic()>deadline:
                    raise TimeoutError()
                start,end=match.span()
                if start==end:
                    raise RuleExecutionError('Une règle produit une correspondance vide. Corrigez-la avant de poursuivre.')
                if len(hits)>=max_hits:
                    raise RuleExecutionError('Trop de correspondances de règles globales. Réduisez le texte ou précisez les règles.')
                hits.append({'start':start,'end':end,'category':rule['category'],
                    'secret':rule['secret'] or rule['category'] in SECRET_CATEGORIES,
                    'reason':'Règle globale : '+rule['name'],'score':1.0,'_priority':4})
    except TimeoutError:
        raise RuleExecutionError('Délai des règles globales dépassé. Réduisez le texte ou faites corriger les règles.') from None
    except (regex.error, RecursionError, OverflowError):
        raise RuleExecutionError('Une règle globale est non valide.') from None
    return hits
