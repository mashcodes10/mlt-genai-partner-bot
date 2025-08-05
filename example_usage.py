#!/usr/bin/env python3
"""
SEC EDGAR API Client - Example Usage

This script demonstrates how to use the enhanced SEC EDGAR client to:
1. Look up company information by ticker
2. Find and retrieve 10-Q and 10-K filings  
3. Download filing documents
4. Search filings by date range

Run with: python example_usage.py
"""

from cik_module import SECEDGARClient


def main():
    print("SEC EDGAR API Client - Example Usage")
    print("=" * 50)
    
    # Initialize the client with proper user agent
    client = SECEDGARClient(
        use_cache=True,
        user_agent="Example-SEC-Client your-email@example.com"
    )
    
    # Example 1: Look up company by ticker
    print("\n📊 Example 1: Company Lookup")
    ticker = "AAPL"
    company_info = client.ticker_to_cik(ticker)
    if company_info:
        cik, name, ticker_symbol = company_info
        print(f"   Company: {name}")
        print(f"   CIK: {cik}")
        print(f"   Ticker: {ticker_symbol}")
    
    # Example 2: Get latest 10-Q filing
    print("\n📄 Example 2: Latest 10-Q Filing")
    latest_10q = client.get_latest_10q(ticker)
    if latest_10q:
        print(f"   Latest 10-Q filed: {latest_10q['filingDate']}")
        print(f"   Document: {latest_10q['primaryDocument']}")
        print(f"   URL: {latest_10q['url']}")
    
    # Example 3: Get latest 10-K filing
    print("\n📄 Example 3: Latest 10-K Filing")
    latest_10k = client.get_latest_10k(ticker)
    if latest_10k:
        print(f"   Latest 10-K filed: {latest_10k['filingDate']}")
        print(f"   Document: {latest_10k['primaryDocument']}")
        print(f"   URL: {latest_10k['url']}")
    
    # Example 4: Find multiple recent 10-Q filings
    print("\n Example 4: Recent 10-Q Filings")
    if company_info:
        cik = company_info[0]
        recent_10qs = client.find_filings(cik, "10-Q", limit=5)
        for i, filing in enumerate(recent_10qs, 1):
            print(f"   {i}. {filing['filingDate']} - {filing['accessionNumber']}")
    
    # Example 5: Get company facts (financial data)
    print("\n💰 Example 5: Company Facts")
    if company_info:
        facts = client.get_company_facts(cik)
        if facts:
            taxonomies = list(facts.get('facts', {}).keys())
            print(f" Available financial data taxonomies: {', '.join(taxonomies)}")
        else:
            print(" No company facts data available")
    
    # Example 6: Search filings by date range
    print("\n Example 6: Search Filings by Date")
    if company_info:
        date_filtered = client.search_filings_by_date(
            cik, "10-Q", "2024-01-01", "2024-12-31"
        )
        print(f" Found {len(date_filtered)} 10-Q filings in 2024:")
        for filing in date_filtered[:3]:  # Show first 3
            print(f"   • {filing['filingDate']} - {filing['accessionNumber']}")
    
    # Example 7: Download a filing (first few hundred characters)
    print("\n Example 7: Download Filing Content")
    if latest_10q:
        print(" Downloading latest 10-Q content...")
        content = client.download_filing(latest_10q)
        if content:
            # Show first 500 characters of the filing
            preview = content[:500].replace('\n', ' ').replace('\r', ' ')
            print(f"   Downloaded {len(content):,} characters")
            print(f"   Preview: {preview}...")
        else:
            print(" Failed to download filing")
    
    print("\n Example completed! The SEC EDGAR client can now:")
    print("   Look up companies by ticker symbol")
    print("   Find and retrieve 10-K/10-Q filings")
    print("   Download filing documents")
    print("   Search filings by date range")
    print("   Access company financial facts")


if __name__ == "__main__":
    main()