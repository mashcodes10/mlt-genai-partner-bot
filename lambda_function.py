"""
AWS Lambda Function: SEC Filing Question Answering with Claude 3 Sonnet
API Gateway Compatible Version

This Lambda function takes a question, company ticker, and year as input,
retrieves the latest 10-K or 10-Q document, and uses AWS Bedrock Claude 3 Sonnet
to answer the question with the document as context.

Expected Input (API Gateway):
{
  "body": "{\"question\": \"How much did Amazon invest in Anthropic?\", \"ticker\": \"AMZN\", \"year\": \"2024\"}"
}

Expected Input (Direct Lambda):
{
  "question": "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?",
  "ticker": "AMZN",
  "year": "2024"
}
"""

import json
import boto3
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import re
import os


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function that supports both API Gateway and direct invocation.
    
    Args:
        event: Lambda event (API Gateway format or direct)
        context: Lambda context object
        
    Returns:
        Dict with the analysis results (API Gateway format if needed)
    """
    try:
        # Parse input based on event source
        if 'body' in event:
            # API Gateway event
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
            
            question = body.get('question')
            ticker = body.get('ticker')
            year = body.get('year')
            form_type = body.get('form_type', '10-Q')
            is_api_gateway = True
        else:
            # Direct Lambda invocation
            question = event.get('question')
            ticker = event.get('ticker')
            year = event.get('year')
            form_type = event.get('form_type', '10-Q')
            is_api_gateway = False
        
        # Validate input
        if not all([question, ticker, year]):
            error_response = {
                'success': False,
                'error': 'Missing required parameters: question, ticker, year',
                'timestamp': datetime.now().isoformat()
            }
            
            if is_api_gateway:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps(error_response)
                }
            else:
                return error_response
        
        # Initialize clients
        sec_client = SECEDGARClient()
        bedrock_client = BedrockClaudeClient()
        
        # Step 1: Get company information
        company_info = sec_client.ticker_to_cik(ticker)
        if not company_info:
            error_response = {
                'success': False,
                'error': f'Company not found for ticker: {ticker}',
                'timestamp': datetime.now().isoformat()
            }
            
            if is_api_gateway:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps(error_response)
                }
            else:
                return error_response
        
        cik, company_name, ticker_symbol = company_info
        
        # Step 2: Get latest filing
        submissions = sec_client.get_company_submissions(cik)
        if not submissions:
            error_response = {
                'success': False,
                'error': f'No submissions found for {company_name}',
                'timestamp': datetime.now().isoformat()
            }
            
            if is_api_gateway:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps(error_response)
                }
            else:
                return error_response
        
        # Step 3: Find appropriate filing
        filings = sec_client.find_filings(
            submissions, 
            form_types=[form_type], 
            start_year=int(year),
            end_year=int(year)
        )
        
        if not filings:
            error_response = {
                'success': False,
                'error': f'No {form_type} filings found for {company_name} in {year}',
                'timestamp': datetime.now().isoformat()
            }
            
            if is_api_gateway:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps(error_response)
                }
            else:
                return error_response
        
        # Get the most recent filing
        latest_filing = filings[0]
        
        # Step 4: Download filing content
        filing_content = sec_client.download_filing(
            latest_filing['accessionNumber'],
            latest_filing['primaryDocument']
        )
        
        if not filing_content:
            error_response = {
                'success': False,
                'error': 'Failed to download filing content',
                'timestamp': datetime.now().isoformat()
            }
            
            if is_api_gateway:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps(error_response)
                }
            else:
                return error_response
        
        # Step 5: Generate AI response
        ai_response = bedrock_client.generate_response(question, filing_content)
        
        if not ai_response or not ai_response.get('success'):
            error_response = {
                'success': False,
                'error': 'Failed to generate AI response',
                'timestamp': datetime.now().isoformat()
            }
            
            if is_api_gateway:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    },
                    'body': json.dumps(error_response)
                }
            else:
                return error_response
        
        # Step 6: Format successful response
        success_response = {
            'success': True,
            'question': question,
            'ticker': ticker.upper(),
            'year': year,
            'form_type': form_type,
            'company_name': company_name,
            'filing_info': {
                'filingDate': latest_filing['filingDate'],
                'accessionNumber': latest_filing['accessionNumber'],
                'primaryDocument': latest_filing['primaryDocument'],
                'form': latest_filing['form']
            },
            'response': ai_response['response'],
            'usage': ai_response.get('usage', {}),
            'model_id': ai_response.get('model_id'),
            'timestamp': datetime.now().isoformat()
        }
        
        if is_api_gateway:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps(success_response)
            }
        else:
            return success_response
        
    except Exception as e:
        print(f"Error: {str(e)}")
        
        error_response = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        
        if 'body' in event:  # API Gateway
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps(error_response)
            }
        else:
            return error_response


class SECEDGARClient:
    """Self-contained SEC EDGAR API client for Lambda."""
    
    def __init__(self, user_agent: str = "SEC Filing Analysis Bot contact@example.com"):
        self.user_agent = user_agent
        self.base_url = "https://data.sec.gov"
        self.company_tickers_url = f"{self.base_url}/files/company_tickers.json"
        self._company_data = None
    
    def _load_data(self) -> Optional[dict]:
        """Load company tickers data."""
        if self._company_data is not None:
            return self._company_data
            
        response = self._make_request(self.company_tickers_url)
        if response:
            self._company_data = response.json()
            return self._company_data
        return None
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request to SEC with proper headers."""
        # Determine correct host based on URL
        if "data.sec.gov" in url:
            host = "data.sec.gov"
        else:
            host = "www.sec.gov"
            
        headers = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": host
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def ticker_to_cik(self, ticker: str) -> Optional[tuple]:
        """Convert ticker to CIK and get company info."""
        data = self._load_data()
        if not data:
            return None
            
        ticker = ticker.upper()
        for key, company_info in data.items():
            if company_info.get('ticker') == ticker:
                cik = str(company_info['cik_str']).zfill(10)
                company_name = company_info['title']
                return cik, company_name, ticker
        return None
    
    def get_company_submissions(self, cik: str) -> Optional[dict]:
        """Get company submissions from SEC."""
        url = f"{self.base_url}/submissions/CIK{cik}.json"
        response = self._make_request(url)
        return response.json() if response else None
    
    def find_filings(self, submissions: dict, form_types: list, start_year: int = None, end_year: int = None) -> list:
        """Find filings of specified types within date range."""
        filings = []
        
        if 'filings' not in submissions or 'recent' not in submissions['filings']:
            return filings
        
        recent_filings = submissions['filings']['recent']
        
        for i, form in enumerate(recent_filings.get('form', [])):
            if form in form_types:
                filing_date = recent_filings['filingDate'][i]
                filing_year = int(filing_date.split('-')[0])
                
                if start_year and filing_year < start_year:
                    continue
                if end_year and filing_year > end_year:
                    continue
                
                filing_info = {
                    'form': form,
                    'filingDate': filing_date,
                    'accessionNumber': recent_filings['accessionNumber'][i],
                    'primaryDocument': recent_filings['primaryDocument'][i],
                    'reportDate': recent_filings.get('reportDate', [None])[i]
                }
                filings.append(filing_info)
        
        # Sort by filing date (most recent first)
        filings.sort(key=lambda x: x['filingDate'], reverse=True)
        return filings
    
    def download_filing(self, accession_number: str, primary_document: str) -> Optional[str]:
        """Download and extract text from SEC filing."""
        # Clean accession number
        clean_accession = accession_number.replace('-', '')
        
        # Build URL
        url = f"https://www.sec.gov/Archives/edgar/data/{clean_accession[:10]}/{accession_number}/{primary_document}"
        
        response = self._make_request(url)
        if not response:
            return None
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text


class BedrockClaudeClient:
    """AWS Bedrock client for Claude interactions."""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def generate_response(self, question: str, context: str) -> dict:
        """Generate response using Claude with context."""
        # Truncate context if too long (Claude has token limits)
        max_context_length = 150000  # Conservative limit
        if len(context) > max_context_length:
            context = context[:max_context_length] + "...\n[Document truncated due to length]"
        
        prompt = f"""You are a financial analyst AI assistant. You have been provided with a company's SEC filing document. Please answer the following question based ONLY on the information contained in the document.

Question: {question}

Document Content:
{context}

Please provide a clear, concise answer based on the information in the document. If the specific information requested is not available in the document, please state that clearly."""
        
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                })
            )
            
            response_body = json.loads(response['body'].read())
            
            return {
                'success': True,
                'response': response_body['content'][0]['text'],
                'usage': response_body.get('usage', {}),
                'model_id': self.model_id
            }
            
        except Exception as e:
            print(f"Bedrock error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
