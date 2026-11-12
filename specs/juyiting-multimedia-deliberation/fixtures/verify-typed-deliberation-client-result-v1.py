#!/usr/bin/env python3
"""Offline frozen fixture consistency only; no runtime/Provider/DB tests."""
from pathlib import Path
import json,copy,hashlib
ROOT=Path(__file__).resolve().parent

def no_duplicates(pairs):
    d={}
    for k,v in pairs:
        assert k not in d,'duplicate key';d[k]=v
    return d

def text(value):
    assert isinstance(value,str) and value.strip()
    assert not any(0xD800<=ord(c)<=0xDFFF for c in value)

def validate(o,c):
    assert type(o) is dict and set(o)==set(['schemaVersion','kind','text','clarification','proposal'])
    assert type(o['schemaVersion']) is int and o['schemaVersion']==1;text(o['text'])
    if o['kind']=='ANSWER':assert o['clarification'] is None and o['proposal'] is None
    elif o['kind']=='CLARIFY':
        assert o['proposal'] is None
        q=o['clarification'];assert type(q) is dict and set(q)==set(['question','requiredFacts']);text(q['question'])
        a=q['requiredFacts'];assert type(a) is list and a and len(a)==len(set(a)) and set(a)<=set(['SOURCE_SELECTION','REFERENCE_REQUIRED','REQUIREMENT_DETAILS','OPERATION_CHOICE'])
    elif o['kind']=='EXECUTION_PROPOSAL':
        assert o['clarification'] is None
        p=o['proposal'];assert type(p) is dict and set(p)==set(['operation','instruction','sourceRefIds']);text(p['instruction'])
        assert len(p['instruction'])<=4000 and not any(0<=ord(x)<32 or 127<=ord(x)<=159 for x in p['instruction'])
        assert p['operation'] in c['supportedOperations']
        ids=p['sourceRefIds'];assert type(ids) is list and len(ids)==len(set(ids))
        sources={v['sourceRefId']:v for v in c['availableSources']};assert set(ids)<=set(sources)
        assert all(sources[i]['mediaType']=='image' for i in ids)
        if p['operation']=='EDIT_IMAGE':assert len(ids)==1 and sources[ids[0]]['kind']=='CURRENT_CONVERSATION_ASSET'
    else:raise AssertionError('unknown kind')

if __name__=='__main__':
    f=json.loads((ROOT/'typed-deliberation-client-result-v1.json').read_text(),object_pairs_hook=no_duplicates)
    assert f['status']=='FROZEN_EXPECTATIONS_NOT_EXECUTED' and f['actualProvider'] is False
    assert len(f['expectedRuntimeCases'])==24 and all(v['execution']=='NOT_RUN' for v in f['expectedRuntimeCases'])
    for o in f['outcomes']:validate(o,f['dispatchFacts'])
    bad=[]
    for path,value in [('schemaVersion',True),('kind','INSPECT'),('text',''),('proposal',{}),('extra','grant')]:
        o=copy.deepcopy(f['outcomes'][0]);o[path]=value;bad.append(o)
    for path,value in [('operation','EDIT_AUDIO'),('sourceRefIds',['unknown']),('sourceRefIds',['source_1','source_1']),('instruction','red\nblue')]:
        o=copy.deepcopy(f['outcomes'][2]);o['proposal'][path]=value;bad.append(o)
    for o in bad:
        try:validate(o,f['dispatchFacts'])
        except (AssertionError,TypeError,ValueError):pass
        else:raise AssertionError('invalid mutation accepted')
    try:json.loads('{"kind":"ANSWER","kind":"EXECUTION_PROPOSAL"}',object_pairs_hook=no_duplicates)
    except AssertionError:pass
    else:raise AssertionError('duplicate JSON key accepted')
    print('PASS offline: 3 valid union samples, 9 invalid mutations, duplicate JSON rejection; 24 runtime cases NOT_RUN')
