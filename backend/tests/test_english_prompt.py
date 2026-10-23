import pytest
from app.engine import detect
TEXT='''Hi, this is Sarah Johnson from Acme Corp. You can reach me at sarah.johnson@acme.com or on +1 (415) 555-0198.

Our production server 192.168.14.22 is throwing 500s. The failing request used API key sk-abc1234567890XYZlmnop and hit https://api.acme.com/v2/orders.

Customer David Miller (card 4111 1111 1111 1111, SSN 123-45-6789) reported the same issue from 42 Maple Avenue. Please investigate: my handle is @sarah_j.'''

@pytest.mark.parametrize('language',['en','fr'])
def test_reported_english_prompt(language):
    hits=detect(TEXT,language)
    expected={'Sarah Johnson','Acme Corp','sarah.johnson@acme.com','+1 (415) 555-0198','192.168.14.22','sk-abc1234567890XYZlmnop','api.acme.com','David Miller','4111 1111 1111 1111','123-45-6789','42 Maple Avenue','@sarah_j'}
    values={TEXT[h['start']:h['end']] for h in hits}
    assert expected<=values
    assert next(h for h in hits if TEXT[h['start']:h['end']]=='sk-abc1234567890XYZlmnop')['secret']
    for word in ['500s','Customer','from','/v2/orders']:
        start=TEXT.index(word)
        assert not any(h['start']<=start<h['end'] for h in hits)

def test_formats_do_not_depend_on_nlp_language_and_have_boundaries():
    text='SSN: 234-56-7890; handle is @other_user; 81 Cedar Road; Example Ltd; +1 212 555 0123; sk-'+('z'*24)
    values={text[h['start']:h['end']] for h in detect(text,use_nlp=False)}
    assert {'234-56-7890','@other_user','81 Cedar Road','Example Ltd','+1 212 555 0123','sk-'+('z'*24)}<=values
    ordinary='Build 123-45-6789; sk-short; 42 requests per second; +1 015 555 0198; orders@localhost'
    hits=detect(ordinary,use_nlp=False)
    assert not any(h['category'] in {'TOKEN','PHONE','US_SSN','ADDRESS','USERNAME'} for h in hits)
