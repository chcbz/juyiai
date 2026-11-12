#!/usr/bin/env python3
"""Offline wire/fixture checks only. Does not execute DB/API/Web/product cases."""
from pathlib import Path
import json,re,copy
ROOT=Path(__file__).resolve().parent
MAX=9223372036854775807

def decimal(value, positive=False):
    assert isinstance(value,str) and re.match(r'^(0|[1-9][0-9]*)$',value)
    n=int(value);assert n<=MAX and (n>=1 if positive else n>=0)
    return n

def identity(value):
    assert isinstance(value,str) and value and value==value.strip() and len(value)<=100
    assert all(not(0<=ord(c)<32 or 127<=ord(c)<=159) for c in value)

def page(value):
    assert set(value)==set(['schemaVersion','scope','after','through','nextAfter','hasMore','entries'])
    assert type(value['schemaVersion']) is int and value['schemaVersion']==1
    scope=value['scope'];assert set(scope)==set(['conversationId','conversationGeneration','taskId'])
    identity(scope['conversationId']);identity(scope['taskId']);decimal(scope['conversationGeneration'],True)
    a=decimal(value['after']);h=decimal(value['through']);assert a<=h
    assert type(value['hasMore']) is bool and type(value['entries']) is list
    seen=set();last=a
    for entry in value['entries']:
        assert set(entry)==set(['ordinal','request']);o=decimal(entry['ordinal'],True);assert last<o<=h;last=o
        r=entry['request'];assert set(r)==set(['requestId','requestRevision','conversationId','conversationGeneration','userMessageId','state','stateVersion','turns','steps'])
        identity(r['requestId']);assert r['requestId'] not in seen;seen.add(r['requestId'])
        assert r['conversationId']==scope['conversationId'] and r['conversationGeneration']==scope['conversationGeneration']
        decimal(r['requestRevision'],True);decimal(r['userMessageId'],True);decimal(r['stateVersion'])
        assert isinstance(r['state'],str) and r['state'];assert type(r['turns']) is list and type(r['steps']) is list
        for s in r['steps']:
            assert s['taskId']==scope['taskId'];identity(s['stepId']);identity(s['targetAgentId']);decimal(s['stepNumber'],True);decimal(s['assignmentRevision']);decimal(s['stateVersion'])
            assert s['kind'] in ['EXECUTE','INSPECT','CHAT']
    if value['hasMore']:
        assert value['entries'] and value['nextAfter']==value['entries'][-1]['ordinal'] and decimal(value['nextAfter'])>a
    else: assert value['nextAfter'] is None
    if h==0: assert not value['entries'] and not value['hasMore']

f=json.loads((ROOT/'bounty-conversation-request-index-v1.json').read_text());assert f['actualProductExecution']=='NOT_RUN' and f['implementationState']=='NOT_IMPLEMENTED'
assert len(f['cases'])==22 and len(set(c['id'] for c in f['cases']))==22 and all(c['execution']=='NOT_RUN' for c in f['cases'])
base=f['examplePage'];page(base)
empty=copy.deepcopy(base);empty.update(through='0',entries=[]);page(empty)
continuing=copy.deepcopy(base);continuing.update(through='15',hasMore=True,nextAfter='12');page(continuing)
invalid=[]
for key,value in [('after','00'),('through',12),('nextAfter','12'),('hasMore','false'),('through','9223372036854775808')]:
    x=copy.deepcopy(base);x[key]=value;invalid.append(x)
x=copy.deepcopy(base);x['entries'][0]['request']['steps'][0]['taskId']='other_task';invalid.append(x)
x=copy.deepcopy(base);x['entries'][0]['request']['conversationGeneration']='2';invalid.append(x)
x=copy.deepcopy(base);x['entries']*=2;invalid.append(x)
for x in invalid:
    try:page(x)
    except (AssertionError,TypeError,ValueError):pass
    else:raise AssertionError('invalid example accepted')
print('PASS offline wire/fixture: 3 valid shapes, 8 invalid mutations; 22 DB/API/Web cases remain NOT_RUN')
