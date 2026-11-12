#!/usr/bin/env python3
"""Verify exact asset DDL and source read queries on this thread's isolated MySQL.
No production target/connection override, no DROP, and no existing schema reuse.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
import pymysql

API = Path(__file__).resolve().parents[4] / 'api-durable-assets-complete'
SOCKET = '/var/tmp/cyf-jyt-mmd-mysql-20260929-thread01a0dde8/mysql.sock'
DATADIR = '/var/tmp/cyf-jyt-mmd-mysql-20260929-thread01a0dde8/data/'

def read(relative):
    return (API / relative).read_text()

def connection(db=None):
    return pymysql.connect(unix_socket=SOCKET, user='root', database=db,
                           charset='utf8mb4', autocommit=True)

def block(source, prefix):
    found = [text for text in re.findall(r'"""(.*?)"""', source, re.S)
             if text.strip().startswith(prefix)]
    assert len(found) == 1, f'ambiguous SQL source: {prefix}'
    return found[0].strip().replace('?', '%s')

def query(c, sql, args=()):
    with c.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()

def main():
    assert str(Path(SOCKET).resolve(strict=True)) == SOCKET
    sha = subprocess.check_output(['git', '-C', str(API), 'rev-parse', 'HEAD'], universal_newlines=True).strip()
    assert not subprocess.check_output(['git', '-C', str(API), 'status', '--porcelain'], universal_newlines=True).strip()
    schema = read('chat/jia-chat-mapper/src/main/resources/db/chat-deliberation-schema.sql')
    projector = read('chat/jia-chat-service/src/main/java/cn/jia/chat/service/ChatBountyAssetProjector.java')
    archive = read('chat/jia-chat-mapper/src/main/java/cn/jia/chat/archive/conversation/JdbcChatConversationArchiveStore.java')
    database = 'mmd_asset_20260930_01a0dde8_' + sha[:8]
    with connection() as c:
        datadir, version = query(c, 'SELECT @@datadir,VERSION()')[0]
        assert datadir == DATADIR and version.startswith('8.0.'), 'wrong fixture server'
        assert not query(c, 'SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s', (database,)), 'fixture already exists; inspect rather than blind retry'
        query(c, f'CREATE DATABASE `{database}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_bin')
    with connection(database) as c:
        statements = [s.strip() for s in re.sub(r'^--.*$', '', schema, flags=re.M).split(';') if s.strip()]
        for _ in range(2):
            for statement in statements: query(c, statement)
        query(c, """CREATE TABLE chat_conversation (id BIGINT PRIMARY KEY,tenant_id VARCHAR(50),jiacn VARCHAR(50),
          client_id VARCHAR(50),lifecycle_generation BIGINT,deleted_at BIGINT,task_id VARCHAR(100),
          conversation_scope_type VARCHAR(20),conversation_scope_key VARCHAR(150),conversation_type VARCHAR(30))
          ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin""")
        query(c, """CREATE TABLE chat_message (id BIGINT PRIMARY KEY,tenant_id VARCHAR(50),jiacn VARCHAR(50),
          client_id VARCHAR(50),conversation_id VARCHAR(100))
          ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_bin""")
        query(c, "INSERT INTO chat_conversation VALUES (42,'0','owner','client',1,NULL,'task','bounty','task:task','juyiting')")
        query(c, "INSERT INTO chat_message VALUES (100,'0','owner','client','42'),(101,'0','owner','client','42')")
        query(c, """INSERT INTO chat_request (tenant_id,owner_jiacn,client_id,request_id,request_revision,request_digest,
          conversation_id,conversation_generation,user_message_id,aggregate_state,state_version,created_at,updated_at)
          VALUES ('0','owner','client','req',1,'hash','42',1,7,'OUTPUT_COMMITTED',1,1,1)""")
        query(c, """INSERT INTO chat_interaction_step VALUES
          ('step','0','owner','client','req',1,1,'42',1,'task',3,'grant',1,'agent',
           'EXECUTE','OUTPUT_COMMITTED',3,'digest',1,1)""")
        query(c, "INSERT INTO chat_step_execution_link VALUES ('intent','0','owner','client','step','exec','RUNNING',1,1,1)")
        insert = block(projector, 'INSERT INTO chat_conversation_asset')
        row = ('ast_1','0','owner','client','42',1,'req','step','exec','run','output_1',100,'part_1','image','image/png','a'*64,20,1)
        query(c, insert, row)
        find = block(projector, 'SELECT a.asset_id,a.tenant_id')
        args = ('ast_1','ast_1','0','owner','client','42')
        assert len(query(c, find, args)) == 1
        assert query(c, find, ('ast_1','ast_1','0','foreign','client','42')) == ()
        parts = block(projector, 'SELECT CAST(a.message_id AS CHAR)')
        assert len(query(c, parts, ('0','owner','client','42'))) == 1
        assert query(c, parts, ('0','foreign','client','42')) == ()
        source = block(archive, 'SELECT a.asset_id,a.revision')
        source_args = ('0','0','owner','owner','client','client','42','42','42','ast_1','ast_1','ast_1',1)
        assert len(query(c, source, source_args)) == 1, 'saved asset cannot be resolved by actual archive query'
        for mutated, code in [(('ast_dup',)+row[1:],1062),
                              (('ast_orphan',)+row[1:7]+('missing',)+row[8:],1452)]:
            try: query(c, insert, mutated)
            except pymysql.err.IntegrityError as error: assert error.args[0] == code
            else: raise AssertionError(f'expected source uniqueness/FK rejection {code}')
        # Establish an earlier RR snapshot, then prove FOR UPDATE sees another
        # relay's newly committed asset instead of duplicating its result message.
        with connection(database) as reader, connection(database) as writer:
            query(reader, 'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            query(reader, 'START TRANSACTION')
            next_args = ('ast_2','ast_2','0','owner','client','42')
            assert query(reader, find, next_args) == ()
            second = ('ast_2',)+row[1:10]+('output_2',101,'part_2')+row[13:]
            query(writer, insert, second)
            assert query(reader, find, next_args) == (), 'fixture did not establish repeatable-read snapshot'
            assert len(query(reader, find+' FOR UPDATE', next_args)) == 1
            query(reader, 'ROLLBACK')
        query(c, 'UPDATE chat_conversation SET lifecycle_generation=2 WHERE id=42')
        assert query(c, find, args) == ()
        assert query(c, parts, ('0','owner','client','42')) == ()
        assert query(c, source, source_args) == ()
        for statement in statements: query(c, statement)
        assert query(c, 'SELECT COUNT(*) FROM chat_conversation_asset')[0][0] == 2
    print(json.dumps({'apiCommit':sha,'database':database,'serverVersion':version,
        'schemaSha256':hashlib.sha256(schema.encode()).hexdigest(),
        'ddlReentrantPreservesRows':True,'sourceUniqueAndForeignKey':True,
        'exactOwnerAndGenerationIsolation':True,'archiveSourceQuery':True,
        'currentReadSeesConcurrentCommittedAsset':True,
        'limitations':['Synthetic thread-owned MySQL only','No Spring transaction/provider/browser/release evidence']}, indent=2))

if __name__ == '__main__': main()
