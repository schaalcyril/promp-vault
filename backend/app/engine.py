"""Detection in code-point offsets. Inputs and findings are never persisted here."""
import ipaddress
import re
import threading
from bisect import bisect_left
from .custom_rules import match_rules
from functools import lru_cache
import tldextract
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from detect_secrets.settings import default_settings
from detect_secrets.core.scan import scan_line

# Do not fetch the public suffix list during analysis.
tldextract.extract = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)
SECRET_TYPES = {"PASSWORD", "TOKEN", "PRIVATE_KEY", "SECRET"}
SECRET_LOCK = threading.Lock()  # detect-secrets settings are process-global.
PASSWORD_KEY = r"(?:password|passwd|pwd|mot[ _]de[ _]passe)"
TOKEN_KEY = r"(?:api[_ -]?key|api[_ -]?token|access[_ -]?token|client[_ -]?secret)"
VALUE = r'''(?:"(?P<double>(?:\\.|[^"\\])*)"|'(?P<single>(?:\\.|[^'\\])*)'|(?P<bare>[^\s,;<>"'}]+))'''
USER = r"[A-Za-z0-9_](?:[A-Za-z0-9._-]*[A-Za-z0-9_-])?"
RULES = [
    # Conservative, language-independent formats also cover fictional test data.
    ("TOKEN", r"(?<![\w-])sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}(?![\w-])", 0),
    ("PHONE", r"(?<![\w+])\+1[ \t]*(?:\([2-9]\d{2}\)|[2-9]\d{2})[ .-]?[2-9]\d{2}[ .-]?\d{4}(?!\d)", 0),
    ("US_SSN", r"(?i)\b(?:SSN|social[ \t]+security[ \t]+number)[ \t]*(?:[:=][ \t]*)?(\d{3}-\d{2}-\d{4})(?!\d)", 1),
    ("USERNAME", r"(?i)\b(?:handle|username|pseudonyme|pseudo)[ \t]+(?:(?:is|est)[ \t]+)?(@[A-Za-z0-9_]{1,64})(?![\w])", 1),
    ("ADDRESS", r"(?<!\w)\d{1,6}[ \t]+(?:[A-Z][A-Za-z'-]*[ \t]+){1,5}(?:Avenue|Street|Road|Lane|Boulevard|Drive|Court|Way)\b", 0),
    ("ORGANIZATION", r"\b(?:[A-Z][A-Za-z0-9&'-]*[ \t]+){1,4}(?:Corp|Corporation|Inc|Ltd|LLC)\b", 0),
    ("PRIVATE_KEY", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", 0),
    ("TOKEN", r"(?i)\bBearer[ \t]+([A-Za-z0-9._~+/=-]+)", 1),
    ("TOKEN", r"\b(?:gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]+|glpat-[A-Za-z0-9_-]+|sk_(?:test|live)_[A-Za-z0-9]+|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)\b", 0),
    ("USERNAME", rf"\b[A-Za-z][A-Za-z0-9_-]*\\{USER}", 0),
    ("USERNAME", rf"(?i)\b(?:username|user|utilisateur|compte(?:[ \t]+utilisateur)?)[ \t]*[:=][ \t]*[\"']?({USER})", 1),
    ("USERNAME", rf"(?i)\b(?:compte[ \t]+utilisateur|identifiant)[ \t]+est[ \t]+({USER})", 1),
    ("HOSTNAME", r"\b(?:srv|bastion|host|db|node|cluster)[-_][A-Za-z0-9_-]+\b", 0),
    ("MAC", r"(?i)(?<![\w:])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![\w:])", 0),
    ("MAC", r"(?i)(?<![\w-])(?:[0-9a-f]{2}-){5}[0-9a-f]{2}(?![\w-])", 0),
    ("EMAIL", r"(?<![\w.+-])[\w.+-]+@[\w-]+(?:\.[\w-]+)+", 0),
]
STRUCTURED_MAP = {"PHONE_NUMBER":"PHONE", "IBAN_CODE":"IBAN", "CREDIT_CARD":"CARD"}
NLP_MAP = {"PERSON":"PERSON", "LOCATION":"LOCATION"}
FILE_EXTENSIONS = {"json","yaml","yml","xml","py","js","ts","tsx","jsx","txt","log","csv","md","toml","ini","conf","sh"}

@lru_cache(maxsize=1)
def analyzer():
    provider = NlpEngineProvider(nlp_configuration={"nlp_engine_name":"spacy","models":[
        {"lang_code":"fr","model_name":"fr_core_news_sm"},
        {"lang_code":"en","model_name":"en_core_web_sm"}]})
    return AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["fr","en"])

def overlaps(a,b):
    return a['start'] < b['end'] and b['start'] < a['end']

def resolve(candidates):
    """Keep exact strong spans over broad NLP guesses; union actual secret overlaps."""
    intervals=[]
    for h in sorted((h for h in candidates if h['_priority']>=2),key=lambda h:h['start']):
        if intervals and h['start']<intervals[-1][1]:
            intervals[-1]=(intervals[-1][0],max(intervals[-1][1],h['end']))
        else: intervals.append((h['start'],h['end']))
    starts=[a for a,b in intervals]
    def covered(h):
        i=bisect_left(starts,h['end'])-1
        return i>=0 and intervals[i][1]>h['start']
    candidates=[h for h in candidates if h['_priority']>=2 or not covered(h)]
    selected=[]
    for item in sorted(candidates,key=lambda x:(x['start'],-x['end'],-x['_priority'])):
        item=item.copy()
        if selected and overlaps(selected[-1],item):
            prev=selected[-1]
            winner=max((prev,item),key=lambda x:(x['secret'],x['_priority'],x['end']-x['start']))
            start,end=min(prev['start'],item['start']),max(prev['end'],item['end'])
            prev.update(winner);prev.update(start=start,end=end)
        else: selected.append(item)
    for item in selected:item.pop('_priority',None)
    return selected

def detect(text, language='fr', use_nlp=True, progress=None, custom_rules=(), language_info=None):
    summary={'mode':language,'detected':[],'uncertain':False,'unsupported':False}
    if language_info is not None:language_info.update(summary)
    progress=progress or (lambda percent,phase: None)
    progress(1,'Règles techniques')
    candidates=match_rules(text,custom_rules)
    def add(start,end,kind,reason='Règle de format ou de contexte',score=1.0,priority=3):
        if start<end:candidates.append(dict(start=start,end=end,category=kind,reason=reason,score=score,secret=kind in SECRET_TYPES,_priority=priority))
    uri_auth=list(re.finditer(r'[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/@:]+:[^\s/@]+@',text))
    for kind,pattern,group in RULES:
        for m in re.finditer(pattern,text):
            if kind=='EMAIL' and any(u.start() <= m.start() < u.end() for u in uri_auth):
                continue
            add(*m.span(group),kind,priority=5 if kind=='PRIVATE_KEY' else (2 if kind=='HOSTNAME' else 3))
    for kind,key in [('PASSWORD',PASSWORD_KEY),('TOKEN',TOKEN_KEY)]:
        pattern=rf'''(?i)(?<![\w])(?:["']?{key}["']?)(?:[ \t]+(?:utilisé|est))*[ \t]*[:=][ \t]*{VALUE}'''
        for m in re.finditer(pattern,text):
            group=next(g for g in ('double','single','bare') if m.group(g) is not None)
            add(*m.span(group),kind,priority=4)
        # Lexical matching only: never parse XML with external entities enabled.
        for m in re.finditer(rf'(?is)<(?P<tag>{key})\b[^>]*>(?P<value>.*?)</(?P=tag)\s*>',text):
            add(*m.span('value'),kind,priority=4)
    for m in re.finditer(r'[a-zA-Z][a-zA-Z0-9+.-]*://(?P<user>[^\s/@:]+):(?P<pwd>[^\s/@]+)@',text):
        add(*m.span('user'),'USERNAME');add(*m.span('pwd'),'PASSWORD',priority=4)
    for m in re.finditer(rf'(?i)\b(?:identifiants|credentials)[ \t]*:[ \t]*({USER})[ \t]*/[ \t]*([^\s<>]+)',text):
        add(*m.span(1),'USERNAME');add(*m.span(2),'PASSWORD',priority=4)
    # Only an explicit client/company label supports this conservative organization rule.
    for m in re.finditer(r'\b(?:client|société|entreprise|company|customer)[ \t]+([A-ZÀ-ÖØ-Þ][\w-]*(?:[ \t]+[A-ZÀ-ÖØ-Þ][\w-]*)*)',text):
        add(*m.span(1),'ORGANIZATION')
    for m in re.finditer(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,3})?(?![\w/]|\.\d)',text):
        try:ipaddress.ip_interface(m.group())
        except ValueError:continue
        add(*m.span(),'IP')
    # Capture the whole candidate first. Validation must never silently truncate an IPv6.
    for m in re.finditer(r'(?<![\w:])(?:[0-9A-Fa-f]*:){2,}[0-9A-Fa-f:.]*(?:%[\w.-]+)?(?:/\d{1,3})?(?![\w:/])',text):
        value=m.group().rstrip('.')
        try:ipaddress.ip_interface(value)
        except ValueError:continue
        add(m.start(),m.start()+len(value),'IP')
    for m in re.finditer(r'\b(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,63}\b',text):
        value=m.group();before=text[max(0,m.start()-30):m.start()]
        # A filename extension alone is ambiguous. Suppress only in explicit file contexts.
        file_context=re.search(r'(?i)(?:ouvrir|open|fichier|file|puis|et)\s+$',before)
        if value.rsplit('.',1)[-1].lower() in FILE_EXTENSIONS and file_context:continue
        add(*m.span(),'FQDN',priority=3)
    progress(15,'Secrets')
    with SECRET_LOCK, default_settings() as settings:
        settings.disable_plugins('Base64HighEntropyString','HexHighEntropyString')
        settings.disable_filters('detect_secrets.filters.common.is_ignored_due_to_verification_policies','detect_secrets.filters.allowlist.is_line_allowlisted')
        # Cache only within this request. scan_line has no cross-line context.
        @lru_cache(maxsize=512)
        def line_secrets(line):
            return tuple((m.start(),m.end())
                for secret in scan_line(line) if secret.secret_value
                for m in re.finditer(re.escape(secret.secret_value),line))
        offset=0
        last_percent=15
        for line in text.splitlines(keepends=True):
            spans=line_secrets(line) if len(line)<=4096 else line_secrets.__wrapped__(line)
            for start,end in spans:
                add(offset+start,offset+end,'SECRET','Détecteur spécialisé de secrets',priority=2)
            offset+=len(line)
            percent=15+int(20*offset/max(1,len(text)))
            if percent!=last_percent:
                progress(percent,'Secrets');last_percent=percent
    if use_nlp:
        engine=analyzer()
        @lru_cache(maxsize=128)
        def block_hits(chunk,selected_language):
            # A single language pipeline feeds both structured and NLP recognizers.
            artifacts=engine.nlp_engine.process_text(chunk,selected_language)
            structured=engine.analyze(text=chunk,language='en',entities=list(STRUCTURED_MAP),score_threshold=0.5,nlp_artifacts=artifacts)
            names=engine.analyze(text=chunk,language=selected_language,entities=list(NLP_MAP),score_threshold=0.55,nlp_artifacts=artifacts)
            return structured,names
        from .languages import choose,passages
        @lru_cache(maxsize=128)
        def selection(chunk):return choose(chunk)
        chunks=passages(text) if language=='auto' else ((base,text[base:base+20000]) for base in range(0,len(text),18000))
        for base,chunk in chunks:
            progress(35+int(60*base/max(1,len(text))),'Entités FR/EN')
            selected,state=selection(chunk) if language=='auto' else ((language,),language)
            if state in ('fr','en') and state not in summary['detected']:summary['detected'].append(state)
            if state in ('uncertain','unsupported'):summary[state]=True
            structured=[];names=[]
            for selected_language in selected:
                found_structured,found_names=block_hits(chunk,selected_language)
                structured.extend(found_structured);names.extend(found_names)
            for hit in structured:
                add(base+hit.start,base+hit.end,STRUCTURED_MAP[hit.entity_type],'Presidio : '+hit.entity_type,hit.score,2)
            for hit in names:
                if chunk[hit.start:hit.end].lower() in {'authorization','content-type','accept','user-agent','host','cookie'} and chunk[hit.end:].startswith(':'):
                    continue
                start,end=hit.start,hit.end
                if hit.entity_type=='PERSON':
                    label=re.match(r'(?i)(?:customer|client|contact|patient)[ \t]+',chunk[start:end])
                    if label:start+=label.end()
                    affiliation=re.search(r"[ \t]+from[ \t]+",chunk[start:end])
                    if affiliation:end=start+affiliation.start()
                add(base+start,base+end,NLP_MAP[hit.entity_type],'Presidio : '+hit.entity_type,hit.score,1)
        block_hits.cache_clear()
        selection.cache_clear()
        if language_info is not None:language_info.update(summary)
    line_secrets.cache_clear()
    progress(96,'Résolution des détections')
    result=resolve(candidates)
    progress(99,'Préparation du résultat')
    return result
