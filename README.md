# SEC EDGAR API Library

A comprehensive Python client for accessing SEC EDGAR filings and company data. I expanded from a simple CIK lookup tool to a full-featured SEC data retrieval system.
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/7369c525-2d69-4c5e-9b44-13e252c84eb7" />

## 🚀 Features

- **Company Lookup**: Convert ticker symbols to CIK numbers and company information
- **Filing Retrieval**: Find and download 10-K, 10-Q, and other SEC filings
- **Financial Data**: Access company facts and financial metrics
- **Date Filtering**: Search filings within specific date ranges
- **Document Download**: Retrieve full filing documents
- **Caching**: Optional caching for improved performance

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🔧 Requirements

- Python 3.7+
- requests


## 🎯 Quick Start

### Basic Usage

```python
from cik_module import SECEDGARClient

# Initialize the client
client = SECEDGARClient(
    use_cache=True,
    user_agent="YourApp your-email@example.com"  # Required by SEC
)

# Look up a company
company_info = client.ticker_to_cik("AAPL")
print(f"Company: {company_info[1]} (CIK: {company_info[0]})")

# Get latest 10-Q filing
latest_10q = client.get_latest_10q("AAPL")
print(f"Latest 10-Q: {latest_10q['filingDate']}")
print(f"URL: {latest_10q['url']}")
```

### Interactive Mode

```bash
python cik_module.py
```

### Demo Mode

```bash
python cik_module.py demo
```

## 📚 API Reference

### Class: SECEDGARClient

#### Initialization

```python
client = SECEDGARClient(
    use_cache=False,                              # Use cached company tickers
    cache_path="company_tickers.json",            # Cache file path
    user_agent="SEC-API-Client contact@example.com"  # Required by SEC
)
```

#### Core Methods

##### `ticker_to_cik(ticker_symbol: str) -> Optional[Tuple[str, str, str]]`
Convert ticker symbol to CIK, company name, and ticker.

```python
result = client.ticker_to_cik("AAPL")
if result:
    cik, name, ticker = result
    print(f"CIK: {cik}, Name: {name}")
```

##### `get_latest_10q(ticker: str) -> Optional[Dict]`
Get the latest 10-Q filing for a company.

```python
filing = client.get_latest_10q("AAPL")
if filing:
    print(f"Date: {filing['filingDate']}")
    print(f"URL: {filing['url']}")
```

##### `get_latest_10k(ticker: str) -> Optional[Dict]`
Get the latest 10-K filing for a company.

```python
filing = client.get_latest_10k("AAPL")
if filing:
    print(f"Date: {filing['filingDate']}")
    print(f"URL: {filing['url']}")
```

##### `find_filings(cik: str, form_type: str = "10-Q", limit: int = 5) -> List[Dict]`
Find recent filings of a specific type.

```python
# Get Apple's CIK first
company_info = client.ticker_to_cik("AAPL")
cik = company_info[0]

# Find recent 10-Q filings
filings = client.find_filings(cik, "10-Q", limit=5)
for filing in filings:
    print(f"{filing['filingDate']}: {filing['accessionNumber']}")
```

##### `download_filing(filing_info: Dict, save_path: Optional[str] = None) -> Optional[str]`
Download a filing document.

```python
filing = client.get_latest_10q("AAPL")
content = client.download_filing(filing, "aapl_10q.htm")
```

##### `get_company_submissions(cik: str) -> Optional[Dict]`
Get all company submissions data.

```python
submissions = client.get_company_submissions("0000320193")
recent_forms = submissions['filings']['recent']['form']
```

##### `get_company_facts(cik: str) -> Optional[Dict]`
Get company facts (financial metrics).

```python
facts = client.get_company_facts("0000320193")
taxonomies = list(facts['facts'].keys())  # ['dei', 'us-gaap']
```

##### `search_filings_by_date(cik: str, form_type: str, start_date: str, end_date: str) -> List[Dict]`
Search filings within a date range.

```python
filings_2024 = client.search_filings_by_date(
    "0000320193", "10-Q", "2024-01-01", "2024-12-31"
)
```

## 🎮 Interactive Commands

When running in interactive mode (`python cik_module.py`):

- `[ticker]` - Look up company info
- `10q [ticker]` - Get latest 10-Q filing
- `10k [ticker]` - Get latest 10-K filing  
- `demo` - Run demonstration
- `exit` - Quit

## 📊 Example Output

```
🔍 SEC EDGAR Client - Enhanced CIK Lookup
Commands:
  [ticker] - Look up company info
  10q [ticker] - Get latest 10-Q
  10k [ticker] - Get latest 10-K
  demo - Run demonstration
  exit - Quit

➤ AAPL
✅ Apple Inc.
   CIK: 0000320193
   Ticker: AAPL

➤ 10q AAPL
📄 Latest 10-Q for AAPL:
   Date: 2025-08-01
   URL: https://www.sec.gov/Archives/edgar/data/0000320193/000032019325000073/aapl-20250628.htm
```

## 🧪 Testing

Run the test suite:

```bash
python -m pytest tests/ -v
```

## 📄 SEC API Endpoints Used

This library utilizes the following official SEC APIs:

- **Company Tickers**: `https://www.sec.gov/files/company_tickers.json`
- **Company Submissions**: `https://data.sec.gov/submissions/CIK{cik}.json`
- **Company Facts**: `https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json`
- **Filing Documents**: `https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}`

## 🔒 User Agent Requirement

The SEC requires all API requests to include a proper User-Agent header with contact information. Always provide your application name and email:

```python
client = SECEDGARClient(user_agent="MyApp contact@mycompany.com")
```

## ⚠️ Rate Limiting

Please respect SEC's server resources:
- Limit requests to no more than 10 per second
- The client includes appropriate delays
- Consider caching results when possible

## 🔄 Backward Compatibility

The original `CIKLookup` class is maintained as an alias for `SECEDGARClient`:

```python
from cik_module import CIKLookup  # Still works
lookup = CIKLookup(use_cache=True)
```

## 🎯 Use Cases

1. **Financial Analysis**: Download and analyze quarterly/annual reports
2. **Compliance Monitoring**: Track filing schedules and deadlines
3. **Research Automation**: Batch download financial documents
4. **Data Mining**: Extract financial metrics from company facts
5. **Investment Research**: Access historical filings for analysis

## 🛠️ Development

To extend the library:

1. Add new methods to `SECEDGARClient`
2. Follow SEC API documentation
3. Include proper type hints
4. Add corresponding tests
5. Update documentation

## 📚 Resources

- [SEC EDGAR Search](https://www.sec.gov/edgar/search/)
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [How to use EDGAR](https://www.sec.gov/search-filings/edgar-search-assistance/how-do-i-use-edgar)
- [Full Text Search FAQ](https://www.sec.gov/edgar/search/efts-faq.html)

## 📝 License

This project is for educational and research purposes. Please ensure compliance with SEC terms of service when using this library.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

**Happy Filing! **
