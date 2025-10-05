#!/bin/bash
# Deploy to AWS App Runner

set -e

SERVICE_NAME="clintrials-mcp"
REGION="${AWS_REGION:-us-east-1}"

echo "This will create an AWS App Runner service."
echo "App Runner pricing: ~\$5/month for 1 vCPU, 2GB RAM"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Check if service exists
if aws apprunner list-services --region $REGION --query "ServiceSummaryList[?ServiceName=='$SERVICE_NAME'].ServiceName" --output text | grep -q "$SERVICE_NAME"; then
    echo "Service already exists. Use AWS Console to update it."
    echo "Console: https://console.aws.amazon.com/apprunner/home?region=$REGION"
    exit 0
fi

echo "Please create the service via AWS Console:"
echo "1. Go to: https://console.aws.amazon.com/apprunner/home?region=$REGION#/create"
echo "2. Choose 'Source code repository' and connect your GitHub repo"
echo "3. Select 'Use a configuration file' and point to apprunner.yaml"
echo "4. Click 'Create & deploy'"
echo ""
echo "Or use ECR (build Docker image locally):"
echo "1. Build: docker build -t $SERVICE_NAME ."
echo "2. Push to ECR: aws ecr create-repository --repository-name $SERVICE_NAME"
echo "3. Tag & push image"
echo "4. Create App Runner service pointing to ECR"
