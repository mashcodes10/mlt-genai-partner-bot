#!/usr/bin/env python3
"""
SEC EDGAR + AWS Bedrock Integration

This script demonstrates the full workflow:
1. Fetch company 10-Q documents using our SEC EDGAR API
2. Test questions without context
3. Test same questions with full document context
4. Compare and save results

This is the foundation for the Lambda function implementation.
"""

import json
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from bs4 import BeautifulSoup
import re

from cik_module import SECEDGARClient
from bedrock_inference_test import BedrockClaudeClient


class SECBedrockIntegration:
    """Integration class for SEC data retrieval and Bedrock analysis."""
    
    def __init__(self, user_agent: str = "SEC-Bedrock-Integration test@example.com"):
        """
        Initialize the integration.
        
        Args:
            user_agent (str): User agent for SEC API requests
        """
        self.sec_client = SECEDGARClient(
            use_cache=True,
            user_agent=user_agent
        )
        self.bedrock_client = BedrockClaudeClient()
        
    def get_latest_filing(self, ticker: str, form_type: str = "10-Q", year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Get the latest filing for a company.
        
        Args:
            ticker (str): Stock ticker symbol
            form_type (str): Type of filing (10-Q, 10-K)
            year (int, optional): Specific year to filter
            
        Returns:
            Dict with filing information or None if not found
        """
        print(f"🔍 Looking up {form_type} filing for {ticker}")
        
        # Get company info
        company_info = self.sec_client.ticker_to_cik(ticker)
        if not company_info:
            print(f"❌ Company not found for ticker: {ticker}")
            return None
            
        cik, company_name, ticker_symbol = company_info
        print(f"✅ Found company: {company_name} (CIK: {cik})")
        
        # Get submissions data
        submissions = self.sec_client.get_company_submissions(cik)
        if not submissions:
            print(f"❌ No submissions found for {company_name}")
            return None
        
        # Find latest filing
        filings = self.sec_client.find_filings_by_form(submissions, form_type)
        if year:
            # Filter by year
            filings = [f for f in filings if f.get('filingDate', '').startswith(str(year))]
        
        if not filings:
            print(f"❌ No {form_type} filings found for {company_name}")
            return None
        
        latest_filing = filings[0]  # Most recent
        print(f"✅ Found latest {form_type}: {latest_filing['filingDate']} - {latest_filing['accessionNumber']}")
        
        return {
            'company_info': company_info,
            'filing_info': latest_filing,
            'form_type': form_type
        }
    
    def download_filing_content(self, filing_info: Dict[str, Any]) -> Optional[str]:
        """
        Download and extract text content from a filing.
        
        Args:
            filing_info (dict): Filing information from get_latest_filing
            
        Returns:
            String content of the filing or None if failed
        """
        filing_data = filing_info['filing_info']
        accession_number = filing_data['accessionNumber']
        primary_document = filing_data.get('primaryDocument', '')
        
        # Build document URL
        # Remove dashes from accession number for URL path
        accession_path = accession_number.replace('-', '')
        
        # Extract CIK from company info
        cik = filing_info['company_info'][0]
        
        # Build the SEC EDGAR URL
        base_url = "https://www.sec.gov/Archives/edgar/data"
        document_url = f"{base_url}/{cik}/{accession_path}/{primary_document}"
        
        print(f"📥 Downloading filing from: {document_url}")
        
        try:
            response = self.sec_client._make_request(document_url)
            if response and response.status_code == 200:
                print("✅ Successfully downloaded filing")
                return self._extract_text_from_html(response.text)
            else:
                print(f"❌ Failed to download filing: {response.status_code if response else 'No response'}")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading filing: {e}")
            return None
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """
        Extract clean text from HTML filing content.
        
        Args:
            html_content (str): Raw HTML content
            
        Returns:
            Clean text content
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit text size (Claude has token limits)
            # Approximately 4 characters per token, with 100K token limit for Claude 3 Sonnet
            max_chars = 300000  # Conservative limit
            if len(text) > max_chars:
                print(f"⚠️  Truncating document from {len(text)} to {max_chars} characters")
                text = text[:max_chars] + "\n\n[DOCUMENT TRUNCATED]"
            
            return text
            
        except Exception as e:
            print(f"❌ Error extracting text: {e}")
            return html_content  # Return raw content as fallback
    
    def test_question_comparison(self, question: str, filing_content: Optional[str] = None) -> Dict[str, Any]:
        """
        Test a question both with and without context.
        
        Args:
            question (str): Question to ask
            filing_content (str, optional): Document content for context
            
        Returns:
            Dict with both responses for comparison
        """
        print(f"\n🧪 Testing Question: {question}")
        print("-" * 60)
        
        # Test without context
        print("📝 Testing WITHOUT context...")
        no_context_result = self.bedrock_client.ask_question(question)
        
        # Test with context (if provided)
        with_context_result = None
        if filing_content:
            print("📝 Testing WITH context...")
            with_context_result = self.bedrock_client.ask_question(question, filing_content)
        
        return {
            'question': question,
            'no_context': no_context_result,
            'with_context': with_context_result,
            'timestamp': datetime.now().isoformat()
        }


def run_comprehensive_test(ticker: str = "AAPL", year: int = 2024):
    """
    Run a comprehensive test of the SEC + Bedrock integration.
    
    Args:
        ticker (str): Stock ticker to analyze
        year (int): Year to focus on
    """
    print("🚀 SEC EDGAR + AWS Bedrock Comprehensive Test")
    print("=" * 70)
    
    # Initialize integration
    integration = SECBedrockIntegration()
    
    # Step 1: Get latest filing
    filing_info = integration.get_latest_filing(ticker, "10-Q", year)
    if not filing_info:
        print("❌ Could not retrieve filing information")
        return
    
    # Step 2: Download filing content
    filing_content = integration.download_filing_content(filing_info)
    if not filing_content:
        print("❌ Could not download filing content")
        return
    
    print(f"✅ Downloaded filing content: {len(filing_content)} characters")
    
    # Step 3: Define test questions
    test_questions = [
        f"How much did {filing_info['company_info'][1]} invest in Anthropic in Q3 2023 and Q1 2024?",
        f"What were {filing_info['company_info'][1]}'s key financial highlights for the most recent quarter?",
        f"What are the main risk factors mentioned in {filing_info['company_info'][1]}'s latest filing?",
        f"How did {filing_info['company_info'][1]}'s operating income change compared to the previous year?",
        f"What is {filing_info['company_info'][1]}'s outlook for the next quarter?"
    ]
    
    # Step 4: Test each question
    all_results = []
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*20} Question {i}/{len(test_questions)} {'='*20}")
        
        result = integration.test_question_comparison(question, filing_content)
        all_results.append(result)
        
        # Print comparison
        print("\n📊 COMPARISON:")
        print("Without Context:")
        if result['no_context']['success']:
            print(f"✅ {result['no_context']['response'][:200]}...")
        else:
            print(f"❌ {result['no_context']['error']}")
        
        print("\nWith Context:")
        if result['with_context'] and result['with_context']['success']:
            print(f"✅ {result['with_context']['response'][:200]}...")
        elif result['with_context']:
            print(f"❌ {result['with_context']['error']}")
        else:
            print("⚠️  No context test performed")
        
        # Small delay between requests
        time.sleep(2)
    
    # Step 5: Save results
    output_data = {
        'test_info': {
            'ticker': ticker,
            'year': year,
            'company_name': filing_info['company_info'][1],
            'filing_date': filing_info['filing_info']['filingDate'],
            'form_type': filing_info['form_type'],
            'test_timestamp': datetime.now().isoformat()
        },
        'filing_content_length': len(filing_content),
        'total_questions': len(all_results),
        'results': all_results
    }
    
    filename = f"sec_bedrock_test_{ticker}_{year}.json"
    with open(filename, 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Complete test results saved to: {filename}")
    
    return output_data


def main():
    """Main function to run the integration test."""
    print("🎯 Choose a test to run:")
    print("1. Apple (AAPL) 2024")
    print("2. Amazon (AMZN) 2024") 
    print("3. Microsoft (MSFT) 2024")
    print("4. Custom ticker")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        run_comprehensive_test("AAPL", 2024)
    elif choice == "2":
        run_comprehensive_test("AMZN", 2024)
    elif choice == "3":
        run_comprehensive_test("MSFT", 2024)
    elif choice == "4":
        ticker = input("Enter ticker symbol: ").strip().upper()
        year = int(input("Enter year (e.g., 2024): ").strip())
        run_comprehensive_test(ticker, year)
    else:
        print("Running default test with AAPL 2024...")
        run_comprehensive_test("AAPL", 2024)


if __name__ == "__main__":
    main()
