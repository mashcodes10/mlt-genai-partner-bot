#!/usr/bin/env python3
"""
AWS Lambda Deployment Script

This script helps deploy the SEC Filing Question Answering Lambda function
with proper IAM roles, policies, and configuration.
"""

import boto3
import json
import zipfile
import os
import time
from typing import Dict, Any


class LambdaDeployer:
    """Helper class to deploy and manage the Lambda function."""
    
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize AWS clients."""
        self.region = region_name
        self.lambda_client = boto3.client('lambda', region_name=region_name)
        self.iam_client = boto3.client('iam', region_name=region_name)
        self.sts_client = boto3.client('sts', region_name=region_name)
        
        # Configuration
        self.function_name = 'sec-filing-qa-function'
        self.role_name = 'sec-filing-qa-lambda-role'
        self.policy_name = 'sec-filing-qa-lambda-policy'
        
    def get_account_id(self) -> str:
        """Get AWS account ID."""
        return self.sts_client.get_caller_identity()['Account']
    
    def create_iam_role(self) -> str:
        """Create IAM role for Lambda function."""
        print("🔐 Creating IAM role for Lambda function...")
        
        # Trust policy for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Create role
            role_response = self.iam_client.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for SEC Filing Q&A Lambda function'
            )
            
            role_arn = role_response['Role']['Arn']
            print(f"✅ Created IAM role: {role_arn}")
            
            # Attach basic Lambda execution policy
            self.iam_client.attach_role_policy(
                RoleName=self.role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Create and attach Bedrock policy
            bedrock_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream"
                        ],
                        "Resource": [
                            f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                        ]
                    }
                ]
            }
            
            self.iam_client.put_role_policy(
                RoleName=self.role_name,
                PolicyName=self.policy_name,
                PolicyDocument=json.dumps(bedrock_policy)
            )
            
            print("✅ Attached Bedrock access policy")
            
            # Wait for role to be available
            print("⏳ Waiting for IAM role to propagate...")
            time.sleep(10)
            
            return role_arn
            
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            print("ℹ️  IAM role already exists, using existing role")
            role_arn = f"arn:aws:iam::{self.get_account_id()}:role/{self.role_name}"
            return role_arn
        
    def create_deployment_package(self) -> str:
        """Create Lambda deployment package."""
        print("📦 Creating Lambda deployment package...")
        
        zip_filename = 'lambda_deployment.zip'
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add main Lambda function
            zipf.write('lambda_function.py')
            
            # Add requirements if they exist
            if os.path.exists('requirements.txt'):
                zipf.write('requirements.txt')
            
            # Add dependencies from lambda_libs directory
            if os.path.exists('lambda_libs'):
                for root, dirs, files in os.walk('lambda_libs'):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_path = os.path.relpath(file_path, '.')
                        zipf.write(file_path, arc_path)
        
        print(f"✅ Created deployment package: {zip_filename}")
        return zip_filename
    
    def deploy_function(self, role_arn: str, zip_filename: str) -> str:
        """Deploy or update Lambda function."""
        print("🚀 Deploying Lambda function...")
        
        # Read deployment package
        with open(zip_filename, 'rb') as f:
            zip_content = f.read()
        
        function_config = {
            'FunctionName': self.function_name,
            'Runtime': 'python3.9',
            'Role': role_arn,
            'Handler': 'lambda_function.lambda_handler',
            'Code': {'ZipFile': zip_content},
            'Description': 'SEC Filing Question Answering with Claude 3 Sonnet',
            'Timeout': 300,  # 5 minutes
            'MemorySize': 1024,  # 1GB RAM
            'Environment': {
                'Variables': {
                    'PYTHONPATH': '/var/task'
                }
            }
        }
        
        try:
            # Create new function
            response = self.lambda_client.create_function(**function_config)
            function_arn = response['FunctionArn']
            print(f"✅ Created Lambda function: {function_arn}")
            
        except self.lambda_client.exceptions.ResourceConflictException:
            # Function exists, update it
            print("ℹ️  Function exists, updating code...")
            
            # Update function code
            self.lambda_client.update_function_code(
                FunctionName=self.function_name,
                ZipFile=zip_content
            )
            
            # Update function configuration
            config_params = {k: v for k, v in function_config.items() 
                           if k not in ['FunctionName', 'Code']}
            
            self.lambda_client.update_function_configuration(
                FunctionName=self.function_name,
                **config_params
            )
            
            response = self.lambda_client.get_function(FunctionName=self.function_name)
            function_arn = response['Configuration']['FunctionArn']
            print(f"✅ Updated Lambda function: {function_arn}")
        
        return function_arn
    
    def test_function(self) -> Dict[str, Any]:
        """Test the deployed Lambda function."""
        print("🧪 Testing Lambda function...")
        
        test_payload = {
            "question": "How much did Amazon invest in Anthropic in Q3 2023 and Q1 2024?",
            "ticker": "AMZN",
            "year": "2024"
        }
        
        try:
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_payload)
            )
            
            # Parse response
            response_payload = json.loads(response['Payload'].read())
            
            if response_payload.get('success'):
                print("✅ Lambda function test successful!")
                print(f"📊 Response preview: {response_payload['response'][:200]}...")
            else:
                print(f"❌ Lambda function test failed: {response_payload.get('error')}")
            
            return response_payload
            
        except Exception as e:
            print(f"❌ Error testing Lambda function: {e}")
            return {'success': False, 'error': str(e)}
    
    def cleanup(self):
        """Clean up deployment files."""
        print("🧹 Cleaning up deployment files...")
        
        if os.path.exists('lambda_deployment.zip'):
            os.remove('lambda_deployment.zip')
            print("✅ Removed deployment package")


def main():
    """Main deployment function."""
    print("🚀 SEC Filing Q&A Lambda Deployment")
    print("=" * 50)
    
    deployer = LambdaDeployer()
    
    try:
        # Step 1: Create IAM role
        role_arn = deployer.create_iam_role()
        
        # Step 2: Create deployment package
        zip_filename = deployer.create_deployment_package()
        
        # Step 3: Deploy function
        function_arn = deployer.deploy_function(role_arn, zip_filename)
        
        # Step 4: Test function
        test_result = deployer.test_function()
        
        # Step 5: Cleanup
        deployer.cleanup()
        
        print("\n🎉 Deployment Complete!")
        print(f"Function ARN: {function_arn}")
        print(f"Function Name: {deployer.function_name}")
        print(f"Region: {deployer.region}")
        
        if test_result.get('success'):
            print("✅ Function is working correctly")
        else:
            print("⚠️  Function deployed but test failed - check CloudWatch logs")
        
        # Provide usage example
        print("\n📖 Usage Example:")
        print("aws lambda invoke \\")
        print(f"  --function-name {deployer.function_name} \\")
        print("  --payload '{")
        print('    "question": "What were the key highlights this quarter?",')
        print('    "ticker": "AAPL",')
        print('    "year": "2024"')
        print("  }' \\")
        print("  response.json")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        deployer.cleanup()


if __name__ == "__main__":
    main()
