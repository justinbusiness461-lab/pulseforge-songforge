import unittest,sys,pathlib,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools'))
from certify_mix import amplitude_dbfs
class PeakMath(unittest.TestCase):
 def test_half_scale(self):self.assertAlmostEqual(amplitude_dbfs(.5),-6.020599913279624)
 def test_full_scale(self):self.assertEqual(amplitude_dbfs(1),0)
 def test_silence(self):self.assertIsNone(amplitude_dbfs(0))
if __name__=='__main__':unittest.main()
