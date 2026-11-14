import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from runnable_receipt_verifier import ReceiptError, verify_candidate_receipt, verify_known_bad_receipt

def good_receipt():
    return {
        'verdict': 'PASS',
        'historyOccurrences': 1,
        'artifactHashValid': True,
        'artifactDecodeValid': True,
        'R2StillCurrent': True,
        'pendingRecords': 0,
        'duplicateR1Binding': False,
        'phantomProjectRevision': False,
        'R2OutputMutated': False,
    }

class CandidateReceiptTests(unittest.TestCase):
    def test_good_receipt_passes(self):
        self.assertTrue(verify_candidate_receipt(good_receipt()))

    def test_pass_with_zero_history_fails(self):
        r = good_receipt(); r['historyOccurrences'] = 0
        with self.assertRaisesRegex(ReceiptError, 'historyOccurrences'):
            verify_candidate_receipt(r)

    def test_fail_verdict_rejects(self):
        r = good_receipt(); r['verdict'] = 'FAIL'
        with self.assertRaisesRegex(ReceiptError, 'verdict'):
            verify_candidate_receipt(r)

    def test_invalid_artifact_hash_rejects(self):
        r = good_receipt(); r['artifactHashValid'] = False
        with self.assertRaisesRegex(ReceiptError, 'artifactHashValid'):
            verify_candidate_receipt(r)

    def test_invalid_audio_decode_rejects(self):
        r = good_receipt(); r['artifactDecodeValid'] = False
        with self.assertRaisesRegex(ReceiptError, 'artifactDecodeValid'):
            verify_candidate_receipt(r)

    def test_r2_authority_loss_rejects(self):
        r = good_receipt(); r['R2StillCurrent'] = False
        with self.assertRaisesRegex(ReceiptError, 'R2StillCurrent'):
            verify_candidate_receipt(r)

    def test_nonterminal_pending_rejects(self):
        r = good_receipt(); r['pendingRecords'] = 1
        with self.assertRaisesRegex(ReceiptError, 'pendingRecords'):
            verify_candidate_receipt(r)

    def test_duplicate_binding_rejects(self):
        r = good_receipt(); r['duplicateR1Binding'] = True
        with self.assertRaisesRegex(ReceiptError, 'duplicateR1Binding'):
            verify_candidate_receipt(r)

    def test_phantom_revision_rejects(self):
        r = good_receipt(); r['phantomProjectRevision'] = True
        with self.assertRaisesRegex(ReceiptError, 'phantomProjectRevision'):
            verify_candidate_receipt(r)

    def test_r2_output_mutation_rejects(self):
        r = good_receipt(); r['R2OutputMutated'] = True
        with self.assertRaisesRegex(ReceiptError, 'R2OutputMutated'):
            verify_candidate_receipt(r)

    def test_missing_required_fact_rejects(self):
        r = good_receipt(); del r['phantomProjectRevision']
        with self.assertRaisesRegex(ReceiptError, 'phantomProjectRevision'):
            verify_candidate_receipt(r)

class KnownBadReceiptTests(unittest.TestCase):
    def test_known_bad_baseline_is_detected(self):
        r = {
            'verdict': 'FAIL', 'historyOccurrences': 0,
            'artifactHashValid': True, 'artifactDecodeValid': True,
            'R2StillCurrent': True, 'pendingRecords': 0,
        }
        self.assertTrue(verify_known_bad_receipt(r))

    def test_known_bad_control_must_not_be_false_green(self):
        r = {
            'verdict': 'PASS', 'historyOccurrences': 1,
            'artifactHashValid': True, 'artifactDecodeValid': True,
            'R2StillCurrent': True, 'pendingRecords': 0,
        }
        with self.assertRaisesRegex(ReceiptError, 'negative control'):
            verify_known_bad_receipt(r)

if __name__ == '__main__':
    unittest.main()
