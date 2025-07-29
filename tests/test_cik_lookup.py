import unittest
from cik_module import CIKLookup

class TestCIKLookup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.lookup = CIKLookup(use_cache=True)  # Avoids repeated downloads

    def test_valid_ticker(self):
        result = self.lookup.ticker_to_cik("AAPL")
        self.assertIsNotNone(result)
        self.assertEqual(result[2], "AAPL")
        self.assertEqual(result[1], "Apple Inc.")

    def test_invalid_ticker(self):
        result = self.lookup.ticker_to_cik("FAKETKR")
        self.assertIsNone(result)

    def test_case_insensitive(self):
        result_upper = self.lookup.ticker_to_cik("TSLA")
        result_lower = self.lookup.ticker_to_cik("tsla")
        self.assertEqual(result_upper, result_lower)

if __name__ == "__main__":
    unittest.main()
