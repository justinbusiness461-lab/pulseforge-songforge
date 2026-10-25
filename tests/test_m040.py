import unittest, pathlib, sys, tempfile, importlib.util, hashlib, json
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
import studio_server as server
class SecurityAndObjects(unittest.TestCase):
 def test_foreign_origin(self):
  self.assertFalse(server.authorized_origin('http://localhost.evil.test:8765','localhost:8765'))
 def test_exact_origin(self):
  self.assertTrue(server.authorized_origin('http://localhost:8765','localhost:8765'))
 def test_wrong_port(self):
  self.assertFalse(server.authorized_origin('http://localhost:9999','localhost:8765'))
 def test_bad_origins(self):
  for value in [None,'null','file://localhost','http://localhost:8765/path','http://user@localhost:8765','http://localhost:8765#x']:
   self.assertFalse(server.authorized_origin(value,'localhost:8765'))
 def test_history(self):
  with tempfile.TemporaryDirectory() as td:
   a=server.persist_export(pathlib.Path(td),'master.wav','mixes',b'A')
   b=server.persist_export(pathlib.Path(td),'master.wav','mixes',b'B')
   self.assertNotEqual(a['saved_at'],b['saved_at'])
   self.assertEqual(pathlib.Path(a['saved_at']).read_bytes(),b'A')
   self.assertEqual(pathlib.Path(b['saved_at']).read_bytes(),b'B')
   for row in json.loads((pathlib.Path(td)/'manifest_registry.json').read_text()):
    self.assertEqual(hashlib.sha256(pathlib.Path(row['absolute_path']).read_bytes()).hexdigest(),row['sha256_checksum'][7:])
 def test_tampered_object_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   a=server.persist_export(pathlib.Path(td),'master.wav','mixes',b'A')
   pathlib.Path(a['saved_at']).write_bytes(b'corrupt')
   with self.assertRaises(ValueError):server.persist_export(pathlib.Path(td),'master.wav','mixes',b'A')
 def test_corrupt_ledger_not_reset(self):
  with tempfile.TemporaryDirectory() as td:
   path=pathlib.Path(td)/'manifest_registry.json';path.write_text('broken')
   with self.assertRaises(ValueError):server.persist_export(pathlib.Path(td),'a','mixes',b'A')
   self.assertEqual(path.read_text(),'broken')
 def test_concurrent_processes_keep_history(self):
  import subprocess
  with tempfile.TemporaryDirectory() as td:
   code="import studio_server as s;from pathlib import Path;import sys;s.persist_export(Path(sys.argv[1]),'same.wav','mixes',sys.argv[2].encode())"
   processes=[subprocess.Popen([sys.executable,'-c',code,td,str(i)],cwd=pathlib.Path(server.__file__).parent) for i in range(4)]
   self.assertEqual([p.wait() for p in processes],[0]*4)
   rows=json.loads((pathlib.Path(td)/'manifest_registry.json').read_text());self.assertEqual(len(rows),4)
   for row in rows:self.assertEqual(hashlib.sha256(pathlib.Path(row['absolute_path']).read_bytes()).hexdigest(),row['sha256_checksum'][7:])
 def test_traversal(self):
  with tempfile.TemporaryDirectory() as td:
   for name,sub in [('../escape','mixes'),('/escape','mixes'),('ok','../x'),('..','x'),('x','a/b')]:
    with self.assertRaises(ValueError):server.persist_export(pathlib.Path(td),name,sub,b'x')
if __name__=='__main__':unittest.main()
