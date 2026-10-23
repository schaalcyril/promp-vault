"""Local credential format and interactive generation; never accepts a CLI password."""
import hashlib
import json
import os
import re
from pathlib import Path

def password_hash(password,salt):
    return hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=131072,r=8,p=1,maxmem=256*1024*1024,dklen=64).hex()

def read(path):
    try:
        with Path(path).open('rb') as f:data=f.read(4097)
        if len(data)>4096:raise ValueError()
        value=json.loads(data)
        if set(value)!={'salt','hash'}:raise ValueError()
        if not re.fullmatch('[0-9a-f]{64}',value['salt']) or not re.fullmatch('[0-9a-f]{128}',value['hash']):raise ValueError()
        return value
    except (OSError,ValueError,TypeError,RecursionError):
        raise RuntimeError('Secret superadmin absent ou invalide.') from None

if __name__=='__main__':
    import argparse,getpass,secrets
    parser=argparse.ArgumentParser(description='Créer un fichier de hash scrypt privé (ne jamais le versionner).')
    parser.add_argument('output');args=parser.parse_args()
    password=getpass.getpass('Mot de passe superadmin (15 caractères minimum) : ')
    confirmation=getpass.getpass('Confirmation : ')
    if password!=confirmation or not (len(password.strip())>=15 and len(password)<=256):raise SystemExit('Deux mots de passe identiques de 15 à 256 caractères sont requis.')
    salt=secrets.token_hex(32);value={'salt':salt,'hash':password_hash(password,salt)}
    fd=os.open(args.output,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as f:json.dump(value,f)
    print('Fichier privé créé. Le fournir au déploiement, ne pas le versionner.')
