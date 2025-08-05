import unittest
from cik_module import SECEDGARClient, CIKLookup

class TestSECEDGARClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = SECEDGARClient(
            use_cache=True,
            user_agent="Test-SEC-Client test@example.com"
        )

    def test_backward_compatibility_alias(self):
        """Test that CIKLookup still works as an alias."""
        lookup = CIKLookup(use_cache=True)
        result = lookup.ticker_to_cik("AAPL")
        self.assertIsNotNone(result)

    def test_valid_ticker(self):
        result = self.client.ticker_to_cik("AAPL")
        self.assertIsNotNone(result)
        self.assertEqual(result[2], "AAPL")
        self.assertEqual(result[1], "Apple Inc.")

    def test_invalid_ticker(self):
        result = self.client.ticker_to_cik("FAKETKR")
        self.assertIsNone(result)

    def test_case_insensitive(self):
        result_upper = self.client.ticker_to_cik("TSLA")
        result_lower = self.client.ticker_to_cik("tsla")
        self.assertEqual(result_upper, result_lower)

    def test_get_latest_10q(self):
        """Test getting latest 10-Q filing."""
        filing = self.client.get_latest_10q("AAPL")
        self.assertIsNotNone(filing)
        self.assertEqual(filing["form"], "10-Q")
        self.assertIn("filingDate", filing)
        self.assertIn("url", filing)

    def test_get_latest_10k(self):
        """Test getting latest 10-K filing."""
        filing = self.client.get_latest_10k("AAPL")
        self.assertIsNotNone(filing)
        self.assertEqual(filing["form"], "10-K")
        self.assertIn("filingDate", filing)
        self.assertIn("url", filing)

    def test_find_filings(self):
        """Test finding multiple filings."""
        # Get Apple's CIK
        ticker_info = self.client.ticker_to_cik("AAPL")
        self.assertIsNotNone(ticker_info)
        cik = ticker_info[0]
        
        # Find recent 10-Q filings
        filings = self.client.find_filings(cik, "10-Q", limit=3)
        self.assertGreater(len(filings), 0)
        self.assertLessEqual(len(filings), 3)
        
        # Check filing structure
        for filing in filings:
            self.assertEqual(filing["form"], "10-Q")
            self.assertIn("filingDate", filing)
            self.assertIn("url", filing)

    def test_company_submissions(self):
        """Test getting company submissions data."""
        ticker_info = self.client.ticker_to_cik("AAPL")
        self.assertIsNotNone(ticker_info)
        cik = ticker_info[0]
        
        submissions = self.client.get_company_submissions(cik)
        self.assertIsNotNone(submissions)
        self.assertIn("filings", submissions)
        self.assertIn("recent", submissions["filings"])

if __name__ == "__main__":
    unittest.main()
