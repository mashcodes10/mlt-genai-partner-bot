import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class SECEDGARClient:
    """
    
    
    This client provides functionality to:
    - Look up company CIK numbers by ticker symbol
    - Retrieve company submissions data 
    - Find and fetch 10-K and 10-Q filings
    - Access company facts data
    """
    
    def __init__(self, use_cache=False, cache_path="company_tickers.json", user_agent="SEC-API-Client mashiurrahman17675@gmail.com"):
        """
        Initialize the SEC EDGAR client.
        
        Args:
            use_cache (bool): Whether to use cached company tickers data
            cache_path (str): Path to the cache file for company tickers
            user_agent (str): User agent string for SEC API requests (required by SEC)
        """
        self.company_name_map = {}
        self.ticker_map = {}
        self.user_agent = user_agent
        self.base_url = "https://data.sec.gov"
        self.edgar_base_url = "https://www.sec.gov/Archives/edgar/data"
        self._load_data(use_cache=use_cache, cache_path=cache_path)

    def _load_data(self, use_cache=False, cache_path="company_tickers.json"):
        """Load company ticker to CIK mapping data from SEC."""
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }

        try:
            if use_cache and os.path.exists(cache_path):
                print(f"Loading data from cache: {cache_path}")
                with open(cache_path, "r") as f:
                    data = json.load(f)
            else:
                print("Fetching fresh data from SEC...")
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                with open(cache_path, "w") as f:
                    json.dump(data, f)

            for entry in data.values():
                cik_str = str(entry["cik_str"]).zfill(10)
                name = entry["title"].strip()
                ticker = entry["ticker"].strip().upper()

                self.company_name_map[name.lower()] = (cik_str, name, ticker)
                self.ticker_map[ticker] = (cik_str, name, ticker)

            print(f"Loaded {len(self.ticker_map)} companies.")
        
        except Exception as e:
            print(f"Error loading data: {e}")

    def ticker_to_cik(self, ticker_symbol: str) -> Optional[Tuple[str, str, str]]:
        """
        Convert ticker symbol to CIK, company name, and ticker.
        
        Args:
            ticker_symbol (str): Stock ticker symbol
            
        Returns:
            Optional[Tuple[str, str, str]]: (CIK, company name, ticker) or None if not found
        """
        key = ticker_symbol.strip().upper()
        result = self.ticker_map.get(key)
        if not result:
            print(f"Ticker symbol '{ticker_symbol}' not found.")
        return result
    
    def _make_request(self, url: str) -> Optional[Dict]:
        """Make HTTP request to SEC API."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def get_company_submissions(self, cik: str) -> Optional[Dict]:
        """
        Get all company submissions data for a given CIK.
        
        Args:
            cik (str): Company CIK number (10 digits, zero-padded)
            
        Returns:
            Optional[Dict]: Company submissions data or None if error
        """
        # Ensure CIK is properly formatted (10 digits, zero-padded)
        cik_formatted = str(cik).zfill(10)
        url = f"{self.base_url}/submissions/CIK{cik_formatted}.json"
        return self._make_request(url)
    
    def get_company_facts(self, cik: str) -> Optional[Dict]:
        """
        Get company facts data (financial metrics) for a given CIK.
        
        Args:
            cik (str): Company CIK number
            
        Returns:
            Optional[Dict]: Company facts data or None if error
        """
        cik_formatted = str(cik).zfill(10)
        url = f"{self.base_url}/api/xbrl/companyfacts/CIK{cik_formatted}.json"
        return self._make_request(url)
    
    def find_filings(self, cik: str, form_type: str = "10-Q", limit: int = 5) -> List[Dict]:
        """
        Find recent filings of a specific type for a company.
        
        Args:
            cik (str): Company CIK number
            form_type (str): Type of filing (e.g., "10-Q", "10-K", "8-K")
            limit (int): Maximum number of filings to return
            
        Returns:
            List[Dict]: List of filing information dictionaries
        """
        submissions = self.get_company_submissions(cik)
        if not submissions:
            return []
        
        filings = []
        recent = submissions.get("filings", {}).get("recent", {})
        
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_documents = recent.get("primaryDocument", [])
        
        for i, form in enumerate(forms):
            if form == form_type and len(filings) < limit:
                filings.append({
                    "form": form,
                    "filingDate": filing_dates[i] if i < len(filing_dates) else "",
                    "accessionNumber": accession_numbers[i] if i < len(accession_numbers) else "",
                    "primaryDocument": primary_documents[i] if i < len(primary_documents) else "",
                    "url": self._build_filing_url(cik, accession_numbers[i], primary_documents[i]) if i < len(accession_numbers) and i < len(primary_documents) else ""
                })
        
        return filings
    
    def _build_filing_url(self, cik: str, accession_number: str, primary_document: str) -> str:
        """Build the full URL to access a filing document."""
        
        accession_clean = accession_number.replace("-", "")
        cik_formatted = str(cik).zfill(10)
        return f"{self.edgar_base_url}/{cik_formatted}/{accession_clean}/{primary_document}"
    
    def get_latest_10q(self, ticker: str) -> Optional[Dict]:
        """
        Get the latest 10-Q filing for a company by ticker symbol.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            Optional[Dict]: Latest 10-Q filing info or None if not found
        """
        ticker_info = self.ticker_to_cik(ticker)
        if not ticker_info:
            return None
        
        cik = ticker_info[0]
        filings = self.find_filings(cik, "10-Q", 1)
        return filings[0] if filings else None
    
    def get_latest_10k(self, ticker: str) -> Optional[Dict]:
        """
        Get the latest 10-K filing for a company by ticker symbol.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            Optional[Dict]: Latest 10-K filing info or None if not found
        """
        ticker_info = self.ticker_to_cik(ticker)
        if not ticker_info:
            return None
        
        cik = ticker_info[0]
        filings = self.find_filings(cik, "10-K", 1)
        return filings[0] if filings else None
    
    def download_filing(self, filing_info: Dict, save_path: Optional[str] = None) -> Optional[str]:
        """
        Download a filing document.
        
        Args:
            filing_info (Dict): Filing information dict from find_filings()
            save_path (Optional[str]): Path to save file (optional)
            
        Returns:
            Optional[str]: File content as string or None if error
        """
        url = filing_info.get("url")
        if not url:
            print("No URL found in filing info")
            return None
        
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate"
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            content = response.text
            
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Filing saved to: {save_path}")
            
            return content
        except requests.RequestException as e:
            print(f"Error downloading filing: {e}")
            return None
    
    def search_filings_by_date(self, cik: str, form_type: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Search for filings within a date range.
        
        Args:
            cik (str): Company CIK number
            form_type (str): Type of filing (e.g., "10-Q", "10-K")
            start_date (str): Start date in YYYY-MM-DD format
            end_date (str): End date in YYYY-MM-DD format
            
        Returns:
            List[Dict]: List of filing information dictionaries
        """
        all_filings = self.find_filings(cik, form_type, limit=100)  # Get more filings to filter
        
        filtered_filings = []
        for filing in all_filings:
            filing_date = filing.get("filingDate", "")
            if start_date <= filing_date <= end_date:
                filtered_filings.append(filing)
        
        return filtered_filings


# Backward compatibility alias
CIKLookup = SECEDGARClient


def demo_sec_client():
    """Demonstrate the SEC EDGAR client capabilities."""
    print("SEC EDGAR API Client Demo")
    print("=" * 50)
    
    # Initialize client
    client = SECEDGARClient(
        use_cache=True, 
        user_agent="MLT-Partner-Bot mashiurrahman17675@gmail.com"
    )
    
    # Example ticker
    ticker = "AAPL"
    print(f"\nAnalyzing {ticker}...")
    
    # Get company info
    ticker_info = client.ticker_to_cik(ticker)
    if not ticker_info:
        print(f"Ticker {ticker} not found")
        return
    
    cik, name, ticker_symbol = ticker_info
    print(f"Found: {name} (CIK: {cik})")
    
    # Get latest 10-Q
    print(f"\nFinding latest 10-Q filing...")
    latest_10q = client.get_latest_10q(ticker)
    if latest_10q:
        print(f"Latest 10-Q: {latest_10q['filingDate']}")
        print(f"   Accession: {latest_10q['accessionNumber']}")
        print(f"   URL: {latest_10q['url']}")
    else:
        print(" No 10-Q filings found")
    
    # Get latest 10-K
    print(f"\n Finding latest 10-K filing...")
    latest_10k = client.get_latest_10k(ticker)
    if latest_10k:
        print(f"Latest 10-K: {latest_10k['filingDate']}")
        print(f"   Accession: {latest_10k['accessionNumber']}")
        print(f"   URL: {latest_10k['url']}")
    else:
        print("No 10-K filings found")
    
    
    print(f"\n📋 Recent 10-Q filings:")
    recent_10q = client.find_filings(cik, "10-Q", 3)
    for i, filing in enumerate(recent_10q, 1):
        print(f"   {i}. {filing['filingDate']} - {filing['accessionNumber']}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_sec_client()
    else:
        # Interactive mode for backward compatibility
        client = SECEDGARClient(
            use_cache=True,
            user_agent="MLT-Partner-Bot mashiurrahman17675@gmail.com"
        )

        print("\n SEC EDGAR Client - Enhanced CIK Lookup")
        print("Commands:")
        print("  [ticker] - Look up company info")
        print("  10q [ticker] - Get latest 10-Q")
        print("  10k [ticker] - Get latest 10-K")
        print("  demo - Run demonstration")
        print("  exit - Quit")
        print()
        
        while True:
            user_input = input("➤ ").strip()
            if user_input.lower() == "exit":
                print("Goodbye! 👋")
                break
            elif user_input.lower() == "demo":
                demo_sec_client()
                continue
            elif user_input.lower().startswith("10q "):
                ticker = user_input[4:].strip()
                filing = client.get_latest_10q(ticker)
                if filing:
                    print(f"Latest 10-Q for {ticker}:")
                    print(f"   Date: {filing['filingDate']}")
                    print(f"   URL: {filing['url']}")
                else:
                    print(f"No 10-Q found for {ticker}")
            elif user_input.lower().startswith("10k "):
                ticker = user_input[4:].strip()
                filing = client.get_latest_10k(ticker)
                if filing:
                    print(f"Latest 10-K for {ticker}:")
                    print(f"   Date: {filing['filingDate']}")
                    print(f"   URL: {filing['url']}")
                else:
                    print(f"No 10-K found for {ticker}")
            else:
                # Regular ticker lookup
                result = client.ticker_to_cik(user_input)
                if result:
                    cik, name, ticker = result
                    print(f" {name}")
                    print(f"   CIK: {cik}")
                    print(f"   Ticker: {ticker}")
            print()
