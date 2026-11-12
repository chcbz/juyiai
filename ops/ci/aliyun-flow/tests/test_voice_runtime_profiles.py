import base64
from pathlib import Path
import subprocess
import tempfile
import unittest

CANDIDATE=Path(__file__).resolve().parents[1]/'host/cyf-api-kit'

class VoiceRuntimeProfiles(unittest.TestCase):
 def fixture(self,provider='cliproxy-realtime'):
  real=provider=='cliproxy-realtime'
  return {'JIA_CHAT_VOICE_ENABLED':'true','JIA_CHAT_VOICE_TRANSCRIPTION_ENABLED':'true','JIA_CHAT_VOICE_TRANSCRIPTION_PROVIDER':provider,'JIA_CHAT_VOICE_TRANSCRIPTION_MODEL':'gpt-realtime' if real else 'whisper-1','JIA_CHAT_VOICE_SYNTHESIS_ENABLED':'true','JIA_CHAT_VOICE_SYNTHESIS_PROVIDER':provider,'JIA_CHAT_VOICE_SYNTHESIS_MODEL':'gpt-realtime' if real else 'gpt-4o-mini-tts','JIA_CHAT_VOICE_SYNTHESIS_PROVIDER_VOICE':'alloy','JIA_CHAT_VOICE_IDENTITY_HMAC_SECRET':'test-identity-key-must-stay-independent-32','JIA_CHAT_VOICE_CACHE_ENCRYPTION_KEY':base64.b64encode(b'c'*32).decode(),'JIA_CHAT_VOICE_COMPATIBILITY_GATEWAY_ALLOWLIST':'https://codex.chcbz.net/v1','SPRING_AI_OPENAI_BASE_URL':'https://codex.chcbz.net/v1','SPRING_AI_OPENAI_API_KEY':'test-fixture-not-a-real-key',**({'JIA_CHAT_VOICE_SYNTHESIS_FORMATS':'wav'} if real else {})}
 def run_parser(self,values):
  script=CANDIDATE.read_text().split('if ! VOICE_ENV_ENCODED=',1)[1].split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]
  with tempfile.TemporaryDirectory(prefix='cyf-voice-profile-fixture-') as d:
   p=Path(d)/'voice.env';p.write_text('\n'.join(k+'='+v for k,v in values.items())+'\n')
   return subprocess.run(['python3','-I','-B','-',str(p)],input=script.encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 def check_bad(self,change,remove=()):
  values=self.fixture();values.update(change)
  for k in remove:values.pop(k,None)
  r=self.run_parser(values);self.assertNotEqual(r.returncode,0);self.assertEqual(r.stdout,b'')
 def test_realtime_profile_without_smoke_token_passes(self):
  v=self.fixture();r=self.run_parser(v);self.assertEqual(r.returncode,0,r.stderr)
  assignments=[base64.b64decode(x).decode().split('=',1) for x in r.stdout.splitlines()]
  self.assertEqual(dict(assignments),v)
 def test_legacy_profile_without_smoke_token_passes(self):self.assertEqual(self.run_parser(self.fixture('openai-compatible')).returncode,0)
 def test_optional_smoke_token_is_never_forwarded(self):
  v=self.fixture();v['CYF_VOICE_SMOKE_BEARER_TOKEN']='optional-test-value-not-a-jwt'
  r=self.run_parser(v);self.assertEqual(r.returncode,0,r.stderr)
  assignments=dict(base64.b64decode(x).decode().split('=',1) for x in r.stdout.splitlines())
  self.assertEqual(assignments,{k:x for k,x in v.items() if k!='CYF_VOICE_SMOKE_BEARER_TOKEN'})
 def test_legacy_mp3_explicit_passes(self):
  v=self.fixture('openai-compatible');v['JIA_CHAT_VOICE_SYNTHESIS_FORMATS']='mp3';self.assertEqual(self.run_parser(v).returncode,0)
 def test_mixed_providers_rejected(self):self.check_bad({'JIA_CHAT_VOICE_SYNTHESIS_PROVIDER':'openai-compatible'})
 def test_mixed_models_rejected(self):self.check_bad({'JIA_CHAT_VOICE_TRANSCRIPTION_MODEL':'whisper-1'})
 def test_realtime_mp3_rejected(self):self.check_bad({'JIA_CHAT_VOICE_SYNTHESIS_FORMATS':'mp3'})
 def test_realtime_missing_format_rejected(self):self.check_bad({},['JIA_CHAT_VOICE_SYNTHESIS_FORMATS'])
 def test_unknown_provider_rejected(self):self.check_bad({'JIA_CHAT_VOICE_TRANSCRIPTION_PROVIDER':'unknown'})
 def test_unknown_config_rejected(self):self.check_bad({'JIA_CHAT_VOICE_FOO':'true'})
 def test_untrusted_gateway_rejected(self):self.check_bad({'SPRING_AI_OPENAI_BASE_URL':'https://untrusted.invalid/v1'})
 def test_unsafe_gateway_rejected(self):self.check_bad({'SPRING_AI_OPENAI_BASE_URL':'https://codex.chcbz.net/v1?token=invalid'})
 def test_identity_provider_key_coupling_rejected(self):self.check_bad({'SPRING_AI_OPENAI_API_KEY':self.fixture()['JIA_CHAT_VOICE_IDENTITY_HMAC_SECRET']})
 def test_invalid_cache_key_rejected(self):self.check_bad({'JIA_CHAT_VOICE_CACHE_ENCRYPTION_KEY':'invalid'})

if __name__=='__main__':unittest.main()
