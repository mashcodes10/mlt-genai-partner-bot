# MLT GEN AI Partner Bot - SEC Filing Analysis with AI

A comprehensive system that combines SEC EDGAR API data retrieval with AWS Bedrock Claude 3 Sonnet AI to answer questions about company filings with full document context.

## 🚀 Project Overview

This project demonstrates three key components:

1. **Part 1**: Basic AWS Bedrock inference testing with Claude 3 Sonnet
2. **Part 2**: SEC document retrieval and context-based questioning
3. **Part 3**: AWS Lambda function for automated filing analysis

## 📁 Project Structure

```
MLT GEN AI Partner Bot/
├── 🔧 Core Components
│   ├── cik_module.py                    # Enhanced SEC EDGAR API client
│   ├── bedrock_inference_test.py        # AWS Bedrock Claude 3 testing
│   ├── sec_bedrock_integration.py       # SEC + Bedrock integration
│   └── lambda_function.py               # AWS Lambda implementation
├── 🚀 Deployment & Demo
│   ├── deploy_lambda.py                 # Lambda deployment script
│   ├── project_demo.py                  # Complete project demonstration
│   ├── sec_demo_no_aws.py              # SEC API demo (no AWS required)
│   └── example_usage.py                 # Basic usage examples
├── 📋 Documentation & Config
│   ├── PROJECT_DOCUMENTATION.md         # Comprehensive project docs
│   ├── README.md                        # This file
│   └── requirements.txt                 # Python dependencies
└── 🧪 Testing
    └── tests/test_cik_lookup.py         # Unit tests
```

## 🎯 Key Features

### 🔍 SEC EDGAR Integration
- **Company Lookup**: Convert ticker symbols to CIK numbers and company information
- **Filing Retrieval**: Download 10-K, 10-Q, and other SEC filings
- **Document Processing**: Extract and clean text from HTML filings
- **Date Filtering**: Find filings within specific date ranges
- **Real-time Data**: Access the latest SEC filings

### 🤖 AI-Powered Analysis
- **AWS Bedrock Integration**: Uses Claude 3 Sonnet model for analysis
- **Context-Aware Responses**: Provides full document content as context
- **Comparison Testing**: Compare AI responses with and without context
- **Smart Processing**: Handles large documents within token limits

### ☁️ AWS Lambda Deployment
- **Serverless Architecture**: Deploy as scalable Lambda function
- **RESTful API**: JSON input/output format
- **Security**: Proper IAM roles and policies
- **Error Handling**: Comprehensive error management

## 📦 Installation & Setup

### Prerequisites
- Python 3.9+
- AWS Account with Bedrock access
- AWS CLI configured

### Installation
```bash
# Clone the project
cd "MLT GEN AI Partner Bot"

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure
```

### AWS Bedrock Setup
1. Go to AWS Console → Bedrock → Model Access
2. Request access to "Claude 3 Sonnet" model
3. Wait for approval (usually instant for most accounts)

## 🧪 Quick Start Demo

### Option 1: SEC API Demo (No AWS Required)
```bash
python sec_demo_no_aws.py
```
This demonstrates the SEC EDGAR API functionality without requiring AWS credentials.

### Option 2: Complete Project Demo
```bash
python project_demo.py
```
This runs the full demonstration including AWS Bedrock integration.

### Option 3: Individual Components
```bash
# Test SEC API only
python example_usage.py

# Test Bedrock only
python bedrock_inference_test.py

# Test integration
python sec_bedrock_integration.py
```

## 🎯 Project Parts Explained

### Part 1: Basic Bedrock Inference
Tests Claude 3 Sonnet with various questions to understand its capabilities:

```python
from bedrock_inference_test import BedrockClaudeClient

client = BedrockClaudeClient()
result = client.ask_question("How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?")
```

**Expected Result**: Claude provides general knowledge but lacks specific details about recent investments.

### Part 2: Context-Based Testing
Retrieves SEC documents and provides them as context:

```python
# Get SEC filing
filing_content = retrieve_latest_10q("AMZN", 2024)

# Ask with context
result = client.ask_question(question, filing_content)
```

**Expected Result**: Claude provides accurate, specific information based on the official SEC filing.

### Part 3: Lambda Function
Automated system that combines both components:

```bash
# Deploy Lambda
python deploy_lambda.py

# Test Lambda
aws lambda invoke \
  --function-name sec-filing-qa-function \
  --payload '{"question": "What were the key highlights?", "ticker": "AAPL", "year": "2024"}' \
  response.json
```

## 📊 Example Usage

### Basic SEC Data Retrieval
```python
from cik_module import SECEDGARClient

client = SECEDGARClient(use_cache=True)

# Look up company
company_info = client.ticker_to_cik("AAPL")
cik, name, ticker = company_info

# Find recent 10-Q filings
filings = client.find_filings(cik, "10-Q", limit=5)
print(f"Latest filing: {filings[0]['filingDate']}")
```

### AI Analysis with Context
```python
from lambda_function import lambda_handler

# Simulate Lambda input
event = {
    "question": "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?",
    "ticker": "AMZN", 
    "year": "2024"
}

result = lambda_handler(event, None)
print(result['response'])
```

**Expected Output**:
```
Based on the information provided in Amazon's 10-Q filing:
- Q3 2023: $1.25 billion convertible note investment in Anthropic
- Q1 2024: $2.75 billion second convertible note investment  
- Total investment: $4 billion
```

## 🔧 Configuration

### Environment Variables
```bash
export AWS_REGION=us-east-1
export AWS_PROFILE=default
```

### Custom User Agent (Required for SEC API)
```python
client = SECEDGARClient(
    user_agent="YourCompany contact@yourcompany.com"
)
```

## 📈 Performance & Limits

### SEC API Limits
- **Rate Limiting**: 10 requests per second (built-in delays)
- **Document Size**: Large 10-K files can be 50MB+ 
- **Caching**: Company ticker data cached locally

### AWS Bedrock Limits
- **Context Window**: 100K tokens for Claude 3 Sonnet
- **Output Tokens**: 4K maximum per response
- **Processing Time**: 30-60 seconds for large documents

### Lambda Configuration
- **Memory**: 1GB (recommended for large documents)
- **Timeout**: 5 minutes (for document download and processing)
- **Concurrency**: 10 concurrent executions (default)

## 🛠️ Troubleshooting

### Common Issues

**"Unable to locate credentials"**
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

**"Model access denied"**
- Go to AWS Console → Bedrock → Model Access
- Request access to Claude 3 Sonnet

**"SEC rate limiting"**
- Built-in delays should handle this automatically
- Ensure proper User-Agent header

## 📋 API Reference

### Lambda Input Format
```json
{
  "question": "What were the key financial highlights?",
  "ticker": "AAPL",
  "year": "2024",
  "form_type": "10-Q"
}
```

### Lambda Output Format
```json
{
  "success": true,
  "company_name": "Apple Inc.",
  "filing_info": {
    "filingDate": "2024-08-01",
    "accessionNumber": "0000320193-24-000073"
  },
  "response": "Based on the filing...",
  "usage": {"input_tokens": 45000, "output_tokens": 150},
  "timestamp": "2024-08-15T10:30:00Z"
}
```

## 🔄 Development Workflow

### Testing
```bash
# Run unit tests
python -m pytest tests/

# Test SEC API
python sec_demo_no_aws.py

# Test with AWS (requires credentials)
python project_demo.py
```

### Deployment
```bash
# Deploy Lambda function
python deploy_lambda.py

# Update existing function
aws lambda update-function-code \
  --function-name sec-filing-qa-function \
  --zip-file fileb://lambda_deployment.zip
```

## 🎯 Real-World Applications

- **Financial Analysis**: Automated analysis of earnings reports
- **Risk Assessment**: Extract risk factors from 10-K filings
- **Compliance Monitoring**: Track regulatory changes and impacts
- **Investment Research**: Compare financial metrics across companies
- **Due Diligence**: Automated fact-checking for M&A activities

## 🚀 Future Enhancements

- **Multi-Document Analysis**: Compare filings across quarters
- **Trend Detection**: Identify changes in financial metrics over time
- **Alert System**: Notify on significant filing changes
- **Visualization Dashboard**: Charts and graphs of financial data
- **Batch Processing**: Analyze multiple companies simultaneously

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **SEC** for providing the EDGAR API and data
- **AWS** for Bedrock and Claude 3 Sonnet access
- **Anthropic** for the Claude AI model
- **Open Source Community** for Python libraries and tools

---

**Ready to analyze SEC filings with AI?** Start with `python sec_demo_no_aws.py` to see the system in action!
