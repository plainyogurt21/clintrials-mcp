#!/bin/bash
# Deploy Clinical Trials MCP to AWS Lambda with Function URL

set -e

FUNCTION_NAME="clintrials-mcp"
REGION="${AWS_REGION:-us-east-1}"

echo "Building deployment package..."

# Create clean build directory
rm -rf lambda-build
mkdir -p lambda-build

# Install dependencies for Lambda (x86_64 Linux)
# Use Docker to ensure compatibility with Lambda environment
if command -v docker &> /dev/null; then
    echo "Using Docker to build Lambda-compatible dependencies..."
    docker run --platform linux/amd64 --rm -v "$PWD":/var/task --entrypoint pip public.ecr.aws/lambda/python:3.11 \
        install -r /var/task/requirements-lambda.txt -t /var/task/lambda-build/
else
    echo "Docker not found. Installing dependencies locally (may not work on ARM Mac)..."
    echo "For best compatibility, install Docker and re-run this script."
    if [ -f .venv/bin/pip ]; then
        .venv/bin/pip install --platform manylinux2014_x86_64 --only-binary=:all: \
            -r requirements-lambda.txt -t lambda-build/ 2>/dev/null || \
        .venv/bin/pip install -r requirements-lambda.txt -t lambda-build/
    else
        pip install -r requirements-lambda.txt -t lambda-build/
    fi
fi

# Copy source files
cp mcp_server.py lambda-build/
cp lambda_function.py lambda-build/

# Create zip
cd lambda-build
zip -r ../lambda-deployment.zip . -x "*.pyc" "*__pycache__*"
cd ..

echo "Deployment package created: lambda-deployment.zip"

# Check if function exists
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION 2>/dev/null; then
    echo "Updating existing Lambda function..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda-deployment.zip \
        --region $REGION
else
    echo "Creating new Lambda function..."

    # Create execution role if it doesn't exist
    ROLE_NAME="clintrials-mcp-lambda-role"

    if ! aws iam get-role --role-name $ROLE_NAME 2>/dev/null; then
        echo "Creating IAM role..."
        aws iam create-role \
            --role-name $ROLE_NAME \
            --assume-role-policy-document '{
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }'

        aws iam attach-role-policy \
            --role-name $ROLE_NAME \
            --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

        echo "Waiting for role to be ready..."
        sleep 10
    fi

    ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)

    # Create function
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime python3.11 \
        --role $ROLE_ARN \
        --handler lambda_function.handler \
        --zip-file fileb://lambda-deployment.zip \
        --timeout 60 \
        --memory-size 512 \
        --region $REGION

    echo "Waiting for function to be active..."
    aws lambda wait function-active --function-name $FUNCTION_NAME --region $REGION

    # Create Function URL with CORS
    echo "Creating Function URL..."
    FUNCTION_URL=$(aws lambda create-function-url-config \
        --function-name $FUNCTION_NAME \
        --auth-type NONE \
        --cors "AllowOrigins=*,AllowMethods=GET,AllowMethods=POST,AllowMethods=OPTIONS,AllowHeaders=*,MaxAge=86400" \
        --region $REGION \
        --query 'FunctionUrl' \
        --output text)

    # Add permission for public access
    aws lambda add-permission \
        --function-name $FUNCTION_NAME \
        --statement-id FunctionURLAllowPublicAccess \
        --action lambda:InvokeFunctionUrl \
        --principal "*" \
        --function-url-auth-type NONE \
        --region $REGION
fi

# Get Function URL
FUNCTION_URL=$(aws lambda get-function-url-config \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'FunctionUrl' \
    --output text 2>/dev/null || echo "")

if [ -n "$FUNCTION_URL" ]; then
    echo ""
    echo "✅ Deployment complete!"
    echo ""
    echo "Function URL: $FUNCTION_URL"
    echo "MCP Endpoint: ${FUNCTION_URL}mcp"
    echo ""
    echo "Next steps:"
    echo "1. Test: curl ${FUNCTION_URL}healthz"
    echo "2. Set Cloudflare Worker secret:"
    echo "   npx wrangler secret put BACKEND_URL"
    echo "   # Paste: $FUNCTION_URL"
    echo "3. Deploy Worker:"
    echo "   npx wrangler deploy"
else
    echo "Function deployed. Run this to get the URL:"
    echo "aws lambda get-function-url-config --function-name $FUNCTION_NAME --region $REGION"
fi

# Cleanup
rm -rf lambda-build lambda-deployment.zip
