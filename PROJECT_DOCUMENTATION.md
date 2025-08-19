# MLT GEN AI Partner Bot - SEC Filing Analysis Project

## Overview

This project demonstrates a comprehensive AI-powered system for analyzing SEC filings using AWS Bedrock Claude 3 Sonnet. The system can retrieve company 10-K and 10-Q documents and answer questions about them with full document context.

## Project Structure

```
MLT GEN AI Partner Bot/
├── cik_module.py                    # Enhanced SEC EDGAR API client
├── bedrock_inference_test.py        # AWS Bedrock Claude 3 testing
├── sec_bedrock_integration.py       # SEC + Bedrock integration
├── lambda_function.py               # AWS Lambda implementation
├── deploy_lambda.py                 # Lambda deployment script
├── project_demo.py                  # Complete project demonstration
├── example_usage.py                 # Usage examples
├── requirements.txt                 # Python dependencies
├── company_tickers.json            # SEC company ticker cache
└── tests/                          # Test files
    └── test_cik_lookup.py
```

## Features

### 🔍 SEC EDGAR Integration
- **Company Lookup**: Convert ticker symbols to CIK numbers
- **Filing Retrieval**: Download 10-K, 10-Q, and other SEC filings
- **Document Processing**: Extract and clean text from HTML filings
- **Date Filtering**: Find filings within specific date ranges

### 🤖 AI-Powered Analysis
- **AWS Bedrock Integration**: Uses Claude 3 Sonnet model
- **Context-Aware Responses**: Provides document content as context
- **Comparison Testing**: Compare responses with and without context
- **Token Management**: Handles large documents efficiently

### ☁️ AWS Lambda Deployment
- **Serverless Architecture**: Deploy as Lambda function
- **API Integration**: RESTful input/output format
- **IAM Security**: Proper role and policy configuration
- **Error Handling**: Comprehensive error management

## Part 1: Basic Inference Testing

### Purpose
Test AWS Bedrock Claude 3 Sonnet with various types of questions to understand its capabilities and limitations.

### Implementation
```python
from bedrock_inference_test import BedrockClaudeClient

client = BedrockClaudeClient()
result = client.ask_question("Can you explain a solar eclipse?")
```

### Test Questions
1. "Can you explain a solar eclipse?"
2. "Can you write explain how to write a python module and give sample code?"
3. "Can you explain what the SEC Edgar library is for?"
4. "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?"

### Expected Results
- General knowledge questions answered correctly
- Specific financial questions may lack current information
- Responses saved to JSON for analysis

## Part 2: Context-Based Testing

### Purpose
Demonstrate how providing SEC document context dramatically improves the accuracy of financial question responses.

### Process
1. **Document Retrieval**: Fetch latest 10-Q filing for a company
2. **Content Extraction**: Parse HTML and extract clean text
3. **Context Testing**: Ask the same questions with and without document context
4. **Comparison Analysis**: Compare response accuracy and detail

### Example Comparison

**Question**: "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?"

**Without Context** (Claude's general knowledge):
```
Claude might provide approximate information or indicate uncertainty about specific investment amounts and timing.
```

**With Context** (Using 10-Q document):
```
Based on the information provided in the 10-Q filing:
- Q3 2023: $1.25 billion convertible note investment
- Q1 2024: $2.75 billion second convertible note investment
Total: $4 billion investment in Anthropic
```

## Part 3: Lambda Function Implementation

### Architecture
```
Input (JSON) → Lambda Function → SEC API → Document Download → 
Bedrock Claude → Contextual Response → Output (JSON)
```

### Input Format
```json
{
  "question": "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?",
  "ticker": "AMZN",
  "year": "2024",
  "form_type": "10-Q"
}
```

### Output Format
```json
{
  "success": true,
  "question": "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?",
  "ticker": "AMZN",
  "year": "2024",
  "company_name": "Amazon.com, Inc.",
  "filing_info": {
    "filingDate": "2024-08-01",
    "accessionNumber": "0000320193-24-000073",
    "form": "10-Q"
  },
  "response": "Based on the information provided...",
  "usage": {
    "input_tokens": 45000,
    "output_tokens": 150
  },
  "timestamp": "2024-08-15T10:30:00Z"
}
```

## Setup Instructions

### Prerequisites
1. **AWS Account** with Bedrock access enabled
2. **AWS Credentials** configured locally
3. **Python 3.9+** installed
4. **Required Permissions**:
   - Bedrock model access (Claude 3 Sonnet)
   - Lambda execution permissions
   - IAM role creation (for deployment)

### Installation
```bash
# Clone or download the project
cd "MLT GEN AI Partner Bot"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Verify Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

## Usage Examples

### 1. Run Basic Tests
```bash
python bedrock_inference_test.py
```

### 2. SEC + Bedrock Integration
```bash
python sec_bedrock_integration.py
```

### 3. Complete Demo
```bash
python project_demo.py
```

### 4. Deploy Lambda Function
```bash
python deploy_lambda.py
```

### 5. Test Lambda Locally
```python
from lambda_function import lambda_handler

event = {
    "question": "What were the key financial highlights this quarter?",
    "ticker": "AAPL",
    "year": "2024"
}

result = lambda_handler(event, None)
print(result)
```

### 6. Invoke Deployed Lambda
```bash
aws lambda invoke \
  --function-name sec-filing-qa-function \
  --payload '{
    "question": "What were the main risk factors mentioned?",
    "ticker": "MSFT", 
    "year": "2024"
  }' \
  response.json
```

## Technical Details

### SEC EDGAR API Integration
- **Base URL**: `https://data.sec.gov/`
- **Rate Limiting**: Respectful delays between requests
- **User Agent**: Required for SEC compliance
- **Data Format**: JSON responses for submissions
- **Document Format**: HTML filings converted to text

### AWS Bedrock Configuration
- **Model**: `anthropic.claude-3-sonnet-20240229-v1:0`
- **Region**: `us-east-1` (default, configurable)
- **Token Limits**: 100K context, 4K output tokens
- **Temperature**: 0.1 (low for factual responses)

### Error Handling
- Network timeouts and retries
- Invalid ticker symbol handling
- Missing filing detection
- Bedrock service errors
- Token limit management

### Performance Considerations
- **Document Size**: Large 10-K/10-Q files are truncated
- **Response Time**: 30-60 seconds typical for complete processing
- **Caching**: Company ticker data cached locally
- **Memory**: Lambda configured with 1GB RAM

## Advanced Features

### Custom Form Types
Support for different SEC filing types:
```python
# 10-K Annual Reports
result = get_filing_response("AAPL", "2024", "10-K")

# 8-K Current Reports
result = get_filing_response("AMZN", "2024", "8-K")
```

### Date Range Queries
```python
# Find filings within specific quarters
filings = find_filings_by_date_range(cik, "2024-01-01", "2024-03-31")
```

### Batch Processing
Process multiple companies or questions:
```python
companies = ["AAPL", "AMZN", "MSFT", "GOOGL"]
questions = ["What were the revenue highlights?", "What are the main risks?"]

for ticker in companies:
    for question in questions:
        result = process_filing_question(ticker, 2024, question)
```

## Project Benefits

### 1. **Automated Analysis**
- Eliminate manual document review
- Consistent analysis across companies
- Rapid information extraction

### 2. **Contextual Intelligence**
- Accurate, source-based responses
- Eliminates hallucination issues
- Provides specific filing references

### 3. **Scalable Architecture**
- Serverless deployment
- Handle multiple concurrent requests
- Cost-effective per-use pricing

### 4. **Regulatory Compliance**
- Uses official SEC data sources
- Proper attribution to source documents
- Maintains audit trail

## Future Enhancements

### Planned Features
1. **Multi-Document Analysis**: Compare across multiple filings
2. **Trend Detection**: Identify changes over time
3. **Risk Assessment**: Automated risk factor analysis
4. **Executive Summary**: Generate filing summaries
5. **Alert System**: Notify on significant changes

### Integration Opportunities
1. **S3 Storage**: Cache documents for faster access
2. **DynamoDB**: Store analysis results
3. **API Gateway**: RESTful web service interface
4. **EventBridge**: Trigger analysis on new filings
5. **QuickSight**: Visualization dashboards

## Troubleshooting

### Common Issues

**Bedrock Access Denied**
```
Solution: Request model access in AWS Console → Bedrock → Model Access
```

**SEC Rate Limiting**
```
Solution: Increase delays between requests, use proper User-Agent header
```

**Lambda Timeout**
```
Solution: Increase timeout to 5 minutes, optimize document processing
```

**Large Document Truncation**
```
Solution: Implement smart truncation, focus on relevant sections
```

### Debug Commands
```bash
# Test SEC API access
python -c "from cik_module import SECEDGARClient; print(SECEDGARClient().ticker_to_cik('AAPL'))"

# Test Bedrock access
python -c "from bedrock_inference_test import BedrockClaudeClient; print(BedrockClaudeClient().ask_question('Hello'))"

# Check AWS credentials
aws sts get-caller-identity
```

## Conclusion

This project demonstrates a complete AI-powered financial document analysis system that combines:
- **SEC regulatory data** for authoritative information
- **Advanced AI models** for natural language understanding
- **Cloud architecture** for scalable deployment
- **Practical applications** for financial analysis

The system shows how proper context dramatically improves AI accuracy for specific domain questions, making it a powerful tool for financial analysts, investors, and researchers.
