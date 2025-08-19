#!/usr/bin/env python3
"""
Create API Gateway to expose Lambda function as REST API
"""

import boto3
import json
import time

class APIGatewayCreator:
    """Create and configure API Gateway for SEC Lambda function."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.region = region_name
        self.apigateway = boto3.client('apigateway', region_name=region_name)
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.sts_client = boto3.client('sts', region_name=region_name)
        
        self.api_name = 'SEC-Filing-Analysis-API'
        self.function_name = 'sec-filing-qa-function'
        
    def get_account_id(self) -> str:
        """Get AWS account ID."""
        return self.sts_client.get_caller_identity()['Account']
    
    def create_rest_api(self) -> dict:
        """Create REST API."""
        print("🔧 Creating REST API...")
        
        response = self.apigateway.create_rest_api(
            name=self.api_name,
            description='SEC Filing Analysis API with AI',
            endpointConfiguration={
                'types': ['REGIONAL']
            }
        )
        
        api_id = response['id']
        print(f"✅ Created API: {api_id}")
        return response
    
    def get_root_resource(self, api_id: str) -> str:
        """Get root resource ID."""
        resources = self.apigateway.get_resources(restApiId=api_id)
        for resource in resources['items']:
            if resource['path'] == '/':
                return resource['id']
    
    def create_analyze_resource(self, api_id: str, parent_id: str) -> str:
        """Create /analyze resource."""
        print("📁 Creating /analyze resource...")
        
        response = self.apigateway.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart='analyze'
        )
        
        resource_id = response['id']
        print(f"✅ Created resource: /analyze ({resource_id})")
        return resource_id
    
    def create_post_method(self, api_id: str, resource_id: str):
        """Create POST method."""
        print("🔄 Creating POST method...")
        
        # Create method
        self.apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            authorizationType='NONE',
            requestParameters={},
            requestModels={
                'application/json': 'Empty'
            }
        )
        
        # Enable CORS
        self.apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        print("✅ Created POST method with CORS")
    
    def setup_lambda_integration(self, api_id: str, resource_id: str):
        """Set up Lambda integration."""
        print("🔗 Setting up Lambda integration...")
        
        account_id = self.get_account_id()
        lambda_arn = f"arn:aws:lambda:{self.region}:{account_id}:function:{self.function_name}"
        
        # Create integration
        self.apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        )
        
        # CORS integration
        self.apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={
                'application/json': '{"statusCode": 200}'
            }
        )
        
        # CORS response
        self.apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': False,
                'method.response.header.Access-Control-Allow-Methods': False,
                'method.response.header.Access-Control-Allow-Origin': False
            }
        )
        
        self.apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                'method.response.header.Access-Control-Allow-Methods': "'POST,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )
        
        print("✅ Lambda integration configured")
    
    def add_lambda_permission(self, api_id: str):
        """Add permission for API Gateway to invoke Lambda."""
        print("🔐 Adding Lambda permission...")
        
        account_id = self.get_account_id()
        source_arn = f"arn:aws:execute-api:{self.region}:{account_id}:{api_id}/*/*"
        
        try:
            self.lambda_client.add_permission(
                FunctionName=self.function_name,
                StatementId=f'api-gateway-{api_id}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
            print("✅ Lambda permission added")
        except Exception as e:
            if "ResourceConflictException" in str(e):
                print("ℹ️  Lambda permission already exists")
            else:
                print(f"⚠️  Permission error: {e}")
    
    def deploy_api(self, api_id: str) -> str:
        """Deploy API to prod stage."""
        print("🚀 Deploying API...")
        
        response = self.apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Production deployment'
        )
        
        # Get API URL
        api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod"
        print(f"✅ API deployed: {api_url}")
        return api_url
    
    def create_full_api(self) -> str:
        """Create complete API setup."""
        print("🚀 Creating SEC Filing Analysis API")
        print("=" * 50)
        
        try:
            # Create API
            api_response = self.create_rest_api()
            api_id = api_response['id']
            
            # Get root resource
            root_id = self.get_root_resource(api_id)
            
            # Create /analyze resource
            resource_id = self.create_analyze_resource(api_id, root_id)
            
            # Create POST method
            self.create_post_method(api_id, resource_id)
            
            # Setup Lambda integration
            self.setup_lambda_integration(api_id, resource_id)
            
            # Add Lambda permission
            self.add_lambda_permission(api_id)
            
            # Deploy API
            api_url = self.deploy_api(api_id)
            
            print("\n🎉 API Gateway Setup Complete!")
            print(f"🌐 Your API URL: {api_url}/analyze")
            print(f"📋 API ID: {api_id}")
            
            return api_url
            
        except Exception as e:
            print(f"❌ Error creating API: {e}")
            return None


def main():
    """Create API Gateway for Lambda function."""
    creator = APIGatewayCreator()
    api_url = creator.create_full_api()
    
    if api_url:
        print("\n📖 Usage Examples:")
        print("=" * 50)
        
        print("\n🌐 cURL Example:")
        print(f"""curl -X POST {api_url}/analyze \\
  -H "Content-Type: application/json" \\
  -d '{{
    "question": "What were the main revenue drivers this quarter?",
    "ticker": "AAPL",
    "year": "2024"
  }}'""")
        
        print("\n🐍 Python Example:")
        print(f"""import requests

response = requests.post('{api_url}/analyze', json={{
    'question': 'What are the key risk factors?',
    'ticker': 'TSLA', 
    'year': '2024'
}})

print(response.json())""")
        
        print("\n🌐 JavaScript Example:")
        print(f"""fetch('{api_url}/analyze', {{
  method: 'POST',
  headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{
    question: 'How did revenue perform this quarter?',
    ticker: 'MSFT',
    year: '2024'
  }})
}})
.then(response => response.json())
.then(data => console.log(data));""")


if __name__ == "__main__":
    main()
