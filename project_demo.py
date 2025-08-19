#!/usr/bin/env python3
"""
SEC EDGAR + AWS Bedrock Project Demo

This script demonstrates the complete workflow for the MLT GEN AI Partner Bot project:

Part 1: Basic Bedrock inference testing with Claude 3 Sonnet
Part 2: SEC document retrieval and context-based questioning  
Part 3: Lambda function simulation

Usage:
    python project_demo.py
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Import our modules
from cik_module import SECEDGARClient

try:
    from bedrock_inference_test import BedrockClaudeClient
    BEDROCK_AVAILABLE = True
except ImportError:
    print("Bedrock not available - boto3 may not be configured")
    BEDROCK_AVAILABLE = False


class ProjectDemo:
    """Main demo class showcasing all project components."""
    
    def __init__(self):
        """Initialize demo with all required clients."""
        self.sec_client = SECEDGARClient(
            use_cache=True,
            user_agent="MLT-Demo-Client demo@example.com"
        )
        
        if BEDROCK_AVAILABLE:
            try:
                self.bedrock_client = BedrockClaudeClient()
                self.bedrock_ready = True
            except Exception as e:
                print(f"Bedrock client initialization failed: {e}")
                self.bedrock_ready = False
        else:
            self.bedrock_ready = False
            
        self.demo_results = []
    
    def part1_basic_inference_test(self):
        """Part 1: Test basic Bedrock inference without context."""
        print("\n" + "="*70)
        print("PART 1: Basic AWS Bedrock Inference Test")
        print("="*70)
        
        if not self.bedrock_ready:
            print("Bedrock not available - skipping Part 1")
            print("To enable Bedrock:")
            print("   1. Configure AWS credentials (aws configure)")
            print("   2. Request Bedrock model access in AWS Console")
            print("   3. Ensure you have the required IAM permissions")
            return {}
        
        # Test questions from the project specification
        test_questions = [
            "Can you explain a solar eclipse?",
            "Can you write explain how to write a python module and give sample code?", 
            "Can you explain what the SEC Edgar library is for?",
            "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?"
        ]
        
        results = []
        
        for i, question in enumerate(test_questions, 1):
            print(f"\nQuestion {i}: {question}")
            print("-" * 50)
            
            result = self.bedrock_client.ask_question(question)
            
            if result['success']:
                response = result['response']
                print(f"Response: {response[:200]}...")
                if len(response) > 200:
                    print("   [Response truncated for display]")
                    
                # Save full response
                results.append({
                    'question': question,
                    'response': response,
                    'success': True,
                    'timestamp': result.get('timestamp'),
                    'usage': result.get('usage', {})
                })
            else:
                print(f"Error: {result['error']}")
                results.append({
                    'question': question,
                    'error': result['error'],
                    'success': False
                })
        
        # Save results
        output_file = 'part1_basic_inference_results.json'
        with open(output_file, 'w') as f:
            json.dump({
                'test_type': 'basic_inference',
                'timestamp': datetime.now().isoformat(),
                'total_questions': len(results),
                'results': results
            }, f, indent=2)
        
        print(f"\nPart 1 results saved to: {output_file}")
        return results
    
    def part2_context_based_testing(self, ticker: str = "AMZN", year: int = 2024):
        """Part 2: Test inference with SEC document context."""
        print("\n" + "="*70)
        print("PART 2: SEC Document Context-Based Testing")
        print("="*70)
        
        # Step 1: Retrieve company 10-Q filing
        print(f"Step 1: Retrieving {ticker} 10-Q filing for {year}")
        
        # Get company info
        company_info = self.sec_client.ticker_to_cik(ticker)
        if not company_info:
            print(f"Company not found for ticker: {ticker}")
            return {}
        
        cik, company_name, ticker_symbol = company_info
        print(f"Found: {company_name} (CIK: {cik})")
        
        # Get 10-Q filings
        submissions = self.sec_client.get_company_submissions(cik)
        if not submissions:
            print(f"No submissions found for {company_name}")
            return {}
        
        filings = self.sec_client.find_filings(cik, "10-Q", limit=10)
        year_filings = [f for f in filings if f.get('filingDate', '').startswith(str(year))]
        
        if not year_filings:
            print(f"No 10-Q filings found for {year}")
            return {}
        
        latest_filing = year_filings[0]
        print(f"Latest 10-Q: {latest_filing['filingDate']} - {latest_filing['accessionNumber']}")
        
        # Step 2: Download document (simulate - actual download would be large)
        print(f"\nStep 2: Document Analysis")
        print(f"   Filing Date: {latest_filing['filingDate']}")
        print(f"   Accession Number: {latest_filing['accessionNumber']}")
        print(f"   Primary Document: {latest_filing.get('primaryDocument', 'N/A')}")
        
        # For demo purposes, we'll use a sample context
        sample_context = """
        AMAZON.COM, INC. FORM 10-Q - For the Quarterly Period Ended June 30, 2024
        
        Note 2 — FINANCIAL INSTRUMENTS
        
        Non-Marketable Investments
        
        In Q3 2023, we invested in a $1.25 billion note from Anthropic, PBC, which is convertible to equity. 
        In Q1 2024, we invested $2.75 billion in a second convertible note. The notes are classified as 
        available for sale and reported at fair value with unrealized gains and losses included in 
        "Accumulated other comprehensive income (loss)." The notes are classified as Level 3 assets. 
        We also have a commercial arrangement primarily for the provision of AWS cloud services, 
        which includes the use of AWS chips.
        
        All non-marketable investments are recorded within "Other assets" on our consolidated balance sheets.
        """
        
        # Step 3: Test questions with and without context
        print(f"\nStep 3: Testing Questions (With vs Without Context)")
        
        test_questions = [
            f"How much did {company_name} invest in Anthropic in Q3 2023 and Q1 2024?",
            f"What were {company_name}'s key financial highlights for the most recent quarter?",
            f"What are the main business segments for {company_name}?"
        ]
        
        results = []
        
        for i, question in enumerate(test_questions, 1):
            print(f"\nQuestion {i}: {question}")
            print("-" * 50)
            
            if self.bedrock_ready:
                print("Testing WITHOUT context...")
                no_context_result = self.bedrock_client.ask_question(question)
                
                print("Testing WITH context...")
                with_context_result = self.bedrock_client.ask_question(question, sample_context)
                
                if no_context_result['success']:
                    print(f"No Context: {no_context_result['response'][:150]}...")
                else:
                    print(f"No Context: ERROR - {no_context_result['error']}")
                
                if with_context_result['success']:
                    print(f"With Context: {with_context_result['response'][:150]}...")
                else:
                    print(f"With Context: ERROR - {with_context_result['error']}")
                
                results.append({
                    'question': question,
                    'no_context': no_context_result,
                    'with_context': with_context_result,
                    'company': company_name,
                    'filing_date': latest_filing['filingDate']
                })
            else:
                print("Bedrock not available - skipping question testing")
                results.append({
                    'question': question,
                    'error': 'Bedrock not available',
                    'company': company_name,
                    'filing_date': latest_filing['filingDate']
                })
        
        output_file = f'part2_context_results_{ticker}_{year}.json'
        with open(output_file, 'w') as f:
            json.dump({
                'test_type': 'context_based',
                'timestamp': datetime.now().isoformat(),
                'company_info': {
                    'ticker': ticker,
                    'name': company_name,
                    'cik': cik,
                    'year': year
                },
                'filing_info': latest_filing,
                'results': results
            }, f, indent=2)
        
        print(f"\nPart 2 results saved to: {output_file}")
        return results
    
    def part3_lambda_simulation(self, ticker: str = "AMZN", year: int = 2024):
        """Part 3: Simulate the Lambda function."""
        print("\n" + "="*70)
        print("PART 3: Lambda Function Simulation")
        print("="*70)
        
        lambda_input = {
            "question": "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?",
            "ticker": ticker,
            "year": year
        }
        
        print(f"Lambda Input:")
        print(json.dumps(lambda_input, indent=2))
        
        print(f"\nProcessing...")
        
        if self.bedrock_ready:
            try:
                from lambda_function import lambda_handler
                
                print("Lambda function imported successfully")
                print("Executing lambda_handler...")
                
                result = lambda_handler(lambda_input, None)
                
                print(f"\nLambda Output:")
                if result.get('success'):
                    print(f"Success: {result['success']}")
                    print(f"Company: {result.get('company_name')}")
                    print(f"Filing Date: {result.get('filing_info', {}).get('filingDate')}")
                    print(f"Response: {result['response'][:200]}...")
                    if len(result['response']) > 200:
                        print("   [Response truncated for display]")
                else:
                    print(f"Error: {result.get('error')}")
                
                output_file = f'part3_lambda_simulation_{ticker}_{year}.json'
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                
                print(f"\nPart 3 results saved to: {output_file}")
                return result
                
            except Exception as e:
                print(f"Lambda simulation failed: {e}")
                print("This might be due to missing AWS credentials or Bedrock access")
                return {'success': False, 'error': str(e)}
        else:
            print("Bedrock not available - skipping Lambda simulation")
            return {'success': False, 'error': 'Bedrock not available'}
    
    def run_complete_demo(self):
        """Run the complete project demonstration."""
        print("MLT GEN AI Partner Bot - Complete Project Demo")
        print("=" * 70)
        
        print("\nChecking Prerequisites...")
        print(f"SEC EDGAR Client: Ready")
        if self.bedrock_ready:
            print(f"AWS Bedrock: Ready")
        else:
            print(f"AWS Bedrock: Not Available")
            print("This demo will show SEC integration but skip AI inference")
        
        part1_results = self.part1_basic_inference_test()
        part2_results = self.part2_context_based_testing()
        part3_results = self.part3_lambda_simulation()
        
        print("\n" + "="*70)
        print("DEMO SUMMARY")
        print("="*70)
        
        print(f"Part 1 - Basic Inference: {'Complete' if part1_results else 'Skipped'}")
        print(f"Part 2 - Context Testing: {'Complete' if part2_results else 'Skipped'}")
        print(f"Part 3 - Lambda Simulation: {'Complete' if part3_results and part3_results.get('success') else 'Skipped'}")
        
        if not self.bedrock_ready:
            print("\nTo enable full functionality:")
            print("   1. Configure AWS credentials: aws configure")
            print("   2. Request Bedrock access in AWS Console")
            print("   3. Ensure Claude 3 Sonnet model access")
            print("   4. Re-run this demo")
        
        print(f"\nDemo completed at {datetime.now().isoformat()}")


def main():
    """Main entry point."""
    demo = ProjectDemo()
    demo.run_complete_demo()


if __name__ == "__main__":
    main()
