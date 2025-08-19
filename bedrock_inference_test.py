#!/usr/bin/env python3
"""
AWS Bedrock Claude 3 Sonnet Inference Test

This script demonstrates how to invoke AWS Bedrock using Claude 3 Sonnet
to test various types of questions and responses.

Requirements:
- AWS credentials configured (via AWS CLI, environment variables, or IAM role)
- boto3 library installed
- Bedrock access enabled in your AWS account
"""

import boto3
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime


class BedrockClaudeClient:
    """Client for interacting with AWS Bedrock Claude 3 Sonnet model."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """
        Initialize the Bedrock client.
        
        Args:
            region_name (str): AWS region where Bedrock is available
        """
        self.region_name = region_name
        self.model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
        
        # Initialize Bedrock Runtime client
        # Create a session with the SSO profile
        session = boto3.Session(profile_name='mlt-course')
        self.bedrock_runtime = session.client(
            service_name='bedrock-runtime',
            region_name=region_name
        )
        
    def invoke_model(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.1) -> Dict[str, Any]:
        """
        Invoke Claude 3 Sonnet model with a prompt.
        
        Args:
            prompt (str): The input prompt/question
            max_tokens (int): Maximum tokens in response
            temperature (float): Sampling temperature (0.0-1.0)
            
        Returns:
            Dict containing the model response and metadata
        """
        # Prepare the request body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        try:
            # Invoke the model
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            return {
                'success': True,
                'response': response_body['content'][0]['text'],
                'usage': response_body.get('usage', {}),
                'model_id': self.model_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'model_id': self.model_id,
                'timestamp': datetime.now().isoformat()
            }
    
    def ask_question(self, question: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask a question with optional context.
        
        Args:
            question (str): The question to ask
            context (str, optional): Additional context to provide
            
        Returns:
            Dict containing the response and metadata
        """
        if context:
            prompt = f"Using the information below.\n\n{question}\n\n{context}"
        else:
            prompt = question
            
        return self.invoke_model(prompt, max_tokens=2000)


def test_basic_questions(client: BedrockClaudeClient):
    """Test basic questions without context."""
    print("🧪 Testing Basic Questions (No Context)")
    print("=" * 60)
    
    questions = [
        "Can you explain a solar eclipse?",
        "Can you write explain how to write a python module and give sample code?",
        "Can you explain what the SEC Edgar library is for?",
        "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?",
        "What was Microsoft's revenue growth in their latest quarter?",
        "Explain the key components of a 10-Q filing."
    ]
    
    results = []
    
    for i, question in enumerate(questions, 1):
        print(f"\n📝 Question {i}: {question}")
        print("-" * 40)
        
        result = client.ask_question(question)
        
        if result['success']:
            print(f"✅ Response:\n{result['response']}")
            if 'usage' in result:
                usage = result['usage']
                print(f"📊 Tokens - Input: {usage.get('input_tokens', 'N/A')}, Output: {usage.get('output_tokens', 'N/A')}")
        else:
            print(f"❌ Error: {result['error']}")
        
        results.append({
            'question': question,
            'result': result,
            'question_number': i
        })
        
        # Small delay between requests
        time.sleep(1)
    
    return results


def test_with_context(client: BedrockClaudeClient, context_document: str):
    """Test questions with document context."""
    print("\n🧪 Testing Questions WITH Context")
    print("=" * 60)
    
    # Sample questions that would benefit from context
    context_questions = [
        "How much did the company invest in Anthropic in Q3 2023 and Q1 2024?",
        "What were the key financial highlights for the most recent quarter?",
        "What are the main risk factors mentioned in this filing?",
        "How did the company's operating income change compared to the previous year?"
    ]
    
    results = []
    
    for i, question in enumerate(context_questions, 1):
        print(f"\n📝 Context Question {i}: {question}")
        print("-" * 40)
        
        result = client.ask_question(question, context_document)
        
        if result['success']:
            print(f"✅ Response:\n{result['response']}")
            if 'usage' in result:
                usage = result['usage']
                print(f"📊 Tokens - Input: {usage.get('input_tokens', 'N/A')}, Output: {usage.get('output_tokens', 'N/A')}")
        else:
            print(f"❌ Error: {result['error']}")
        
        results.append({
            'question': question,
            'result': result,
            'question_number': i,
            'has_context': True
        })
        
        # Small delay between requests
        time.sleep(1)
    
    return results


def save_results(results: list, filename: str):
    """Save test results to a JSON file."""
    output_data = {
        'test_timestamp': datetime.now().isoformat(),
        'total_questions': len(results),
        'results': results
    }
    
    with open(filename, 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {filename}")


def main():
    """Main function to run the Bedrock inference tests."""
    print("🚀 AWS Bedrock Claude 3 Sonnet Inference Test")
    print("=" * 60)
    
    # Initialize the client
    try:
        client = BedrockClaudeClient()
        print(f"✅ Bedrock client initialized for region: {client.region_name}")
        print(f"🤖 Using model: {client.model_id}")
    except Exception as e:
        print(f"❌ Failed to initialize Bedrock client: {e}")
        print("\n💡 Make sure you have:")
        print("   - AWS credentials configured")
        print("   - Bedrock access enabled in your AWS account")
        print("   - boto3 library installed")
        return
    
    # Test basic questions without context
    basic_results = test_basic_questions(client)
    
    # Save basic results
    save_results(basic_results, 'bedrock_test_results_no_context.json')
    
    # For context testing, we'll need to integrate with our SEC API
    print("\n🔄 To test with context, we need to fetch a 10-Q document...")
    print("This will be implemented next using our SEC EDGAR API library.")
    
    return basic_results


if __name__ == "__main__":
    main()
