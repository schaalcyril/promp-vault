"""Immutable analysis settings loaded at deployment."""
from pydantic import BaseModel, Field, ConfigDict
class Settings(BaseModel):
    model_config=ConfigDict(extra='forbid')
    default_language: str=Field(default='auto',pattern='^(auto|fr|en)$')
    max_text_mib: int=Field(default=10,ge=1,le=10)
def load():
    from .configuration import current
    config=current()
    return {'definition':config['settings'],'version':config['version']}
