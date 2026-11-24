"""Offline regression of the actual host transaction suffix, not a host installer.
Never import the installer: its top-level preflight opens host locks and systemd.
"""
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time
import types
import unittest
from unittest.mock import patch


SOURCE_SHA = '384d0ab31a1b311057d9a47794e540e92d0fedfc37cb350ac2a9a38816859fde'
FIXED_SHA = '31daffdd43906abacaa2039d8a58ef7119f3caf78c8e27a35071481abe8ce933'
PATCH = Path(__file__).resolve().parents[1] / 'runtime-forward-only.patch'


@unittest.skipUnless(os.environ.get('CYF_TEST_RUNTIME_INSTALL_SOURCE'), 'requires pinned historic host transaction')
class ForwardOnlyTransactionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        raw = Path(os.environ['CYF_TEST_RUNTIME_INSTALL_SOURCE']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SOURCE_SHA)
        copy = self.root / 'install.py'; copy.write_bytes(raw)
        # Apply the same change the host candidate owner reviews; never edit the source.
        for flags in (['--check'], []):
            subprocess.run(['git', 'apply', *flags, str(PATCH)], cwd=self.root, check=True)
        fixed = copy.read_bytes(); self.assertEqual(hashlib.sha256(fixed).hexdigest(), FIXED_SHA)
        self.sources = {'original': raw, 'fixed': fixed}

    def exercise(self, version, fault):
        # Start at the verified, stopped predecessor after state backup. All subsequent
        # program moves, exception handling and final receipt writing are original code.
        tree = ast.parse(self.sources[version]); tx, = [n for n in tree.body if isinstance(n, ast.Try)]
        i, = [i for i,n in enumerate(tx.body) if isinstance(n, ast.Assert) and isinstance(n.msg, ast.Constant) and n.msg.value == 'DONOR_CHANGED']
        tx.body = tx.body[i:]; functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'sha','manifest','atomic'}]
        root = self.root / (version+'-'+fault); root.mkdir(); app,stage,backup,records,task,state = [root / n for n in ('app','stage','backup','records','task','state')]
        for d in (app,stage,backup,records,task,state): d.mkdir()
        (app/'reader').write_bytes(b'old'); (stage/'reader').write_bytes(b'new'); pending=state/'pending'; pending.write_bytes(b'pending fixture revision')
        for n in ('current.json','current.manifest.json'): (records/n).write_bytes(b'{}')
        shutil.copytree(records, backup/'release-records'); starts=[]
        def admin(*args):
            self.assertEqual(args, ('systemctl','start','fixture')); starts.append((app/'reader').read_bytes())
        def validate(args, **kwargs):
            self.assertEqual(fault,'after'); self.assertEqual(args[:2], ['bash',str(app/'runtime/validate.sh')]); raise OSError('validation fault')
        ns=dict(os=os,hashlib=hashlib,stat=stat,json=json,time=time,shutil=shutil,subprocess=types.SimpleNamespace(run=validate,STDOUT=subprocess.STDOUT),
                APP=app,STAGE=stage,BACK=backup,RECORDS=records,TASK=task,CONFIG=root/'config',UNIT='fixture',env={},
                started=time.monotonic(),stopped=True,start_attempted=False,old_saved=False,report={'rollbackPolicy':'forward-only'},
                admin=admin,prop=lambda k: '0' if not starts else '1')
        exec(compile(ast.Module(body=functions,type_ignores=[]),'pinned-helpers','exec'),ns); ns['baseline']=ns['manifest'](app)
        rename=Path.rename
        def inject(path,target):
            if (fault=='before' and path==app) or (fault=='between' and path==stage): raise OSError('rename fault')
            return rename(path,target)
        with patch.object(Path,'rename',inject), contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(OSError,'fault'):
            exec(compile(ast.Module(body=[tx],type_ignores=[]),'pinned-stopped-install','exec'),ns)
        report=json.loads((task/'installation-result.json').read_bytes());self.assertEqual(report['status'],'FAIL')
        self.assertEqual(pending.read_bytes(),b'pending fixture revision'); self.assertEqual((records/'current.json').read_bytes(),b'{}')
        if version=='original':
            self.assertEqual(starts,[b'old']);self.assertTrue(report['oldServiceRestarted']);return
        self.assertEqual(starts,[]);self.assertEqual(report['recovery'],'forward_only_repair_required');self.assertFalse(report['candidateStartAttempted'])
        self.assertEqual(report['predecessorMoved'],fault!='before')
        if fault=='before':self.assertEqual((app/'reader').read_bytes(),b'old')
        else:self.assertEqual((backup/'old-program/reader').read_bytes(),b'old')
        if fault=='between':self.assertFalse(app.exists())
        self.assertEqual(((app if fault=='after' else stage)/'reader').read_bytes(),b'new')

    def test_fault_before_first_move(self):
        for version in self.sources: self.exercise(version,'before')

    def test_fault_between_program_moves(self):
        for version in self.sources: self.exercise(version,'between')

    def test_validation_fault_after_swap(self):
        for version in self.sources: self.exercise(version,'after')
