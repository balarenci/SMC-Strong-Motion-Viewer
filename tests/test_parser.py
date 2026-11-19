"""Basic parser checks. Run: python -m unittest discover -s tests"""
import unittest
import tempfile
from pathlib import Path
from smc_waveform_viewer import read_numeric_data, scaled_values, SMCRecord
import numpy as np

class ParserTests(unittest.TestCase):
    def test_numeric_series(self):
        x = read_numeric_data([' 1.0  2.0  3.0'], 3)
        np.testing.assert_allclose(x, [1, 2, 3])

    def test_g_units(self):
        record = SMCRecord(Path('demo.smc'),1,[],[],[],[],np.array([0.]),np.array([980.665]),1.0,None,'','',False)
        vals, unit = scaled_values(record, 'g')
        self.assertEqual(unit, 'g')
        self.assertAlmostEqual(vals[0], 1.0)

if __name__ == '__main__':
    unittest.main()
