import unittest,numpy as np
from measure import metrics,locality,section_loudness
class NeutralVectors(unittest.TestCase):
 def setUp(self):
  self.rate=48000;t=np.arange(48000)/self.rate;self.s=.5*np.sin(2*np.pi*1000*t);self.dual=np.column_stack([self.s,self.s])
 def test_ffmpeg_reference(self):
  x=np.tile(self.s,3)[:,None];r=section_loudness(x,self.rate)
  self.assertIsNotNone(r['truePeakEstimateDbtp']);self.assertAlmostEqual(r['truePeakEstimateDbtp'],-6.0206,delta=.15);self.assertAlmostEqual(r['integratedLufs'],-9.0,delta=.2)
 def test_silence(self):
  m=metrics(np.zeros((48000,2)),self.rate);self.assertIsNone(m['correlation']);self.assertIsNone(m['samplePeakDbfs']);self.assertEqual(m['silenceWindows'],[[0,48000]])
 def test_dual_mono(self):
  m=metrics(self.dual,self.rate);self.assertAlmostEqual(m['correlation'],1);self.assertIsNone(m['sideToMidDb']);self.assertEqual(m['sideRms'],0)
 def test_antiphase(self):
  m=metrics(np.column_stack([self.s,-self.s]),self.rate);self.assertAlmostEqual(m['correlation'],-1);self.assertEqual(m['midRms'],0);self.assertIsNone(m['monoDownmixDbRelativeToStereoRms'])
 def test_peak_rms(self):
  m=metrics(self.dual,self.rate);self.assertAlmostEqual(m['samplePeakDbfs'],-6.020599913,places=6);self.assertAlmostEqual(m['rmsDbfs'],-9.03089987,places=6)
 def test_gain_step(self):self.assertAlmostEqual(metrics(self.dual*.5,self.rate)['rmsDbfs']-metrics(self.dual,self.rate)['rmsDbfs'],-6.020599913,places=6)
 def test_independent_stereo(self):
  t=np.arange(48000)/self.rate;m=metrics(np.column_stack([self.s,.5*np.sin(2*np.pi*2000*t)]),self.rate);self.assertAlmostEqual(m['correlation'],0,places=10)
 def test_gap(self):
  x=self.dual.copy();x[12000:36000]=0;self.assertEqual(metrics(x,self.rate)['silenceWindows'],[[12000,36000]])
 def test_spectral_band(self):self.assertGreater(metrics(self.dual,self.rate)['spectralEnergyFractions']['500-2000'],.999)
 def test_identical(self):self.assertEqual(locality(self.dual,self.dual,[])['differingRuns'],[])
 def test_local_edit(self):
  b=self.dual.copy();b[100:110]+=0.1;self.assertTrue(locality(self.dual,b,[[100,110]])['outsideExactlyEqual'])
 def test_outside_sample(self):
  b=self.dual.copy();b[111,0]+=1/32768;self.assertFalse(locality(self.dual,b,[[100,110]])['outsideExactlyEqual'])
 def test_invalid_interval(self):
  with self.assertRaises(ValueError):locality(self.dual,self.dual,[[0,48001]])
 def test_mismatch(self):
  with self.assertRaises(ValueError):locality(self.dual,self.dual[:-1],[])
 def test_nonfinite(self):
  with self.assertRaises(ValueError):metrics(np.array([[float('nan')]]),48000)
if __name__=='__main__':unittest.main()
