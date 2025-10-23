#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Deploying Hermes to Google Cloud Run${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/install${NC}"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Using project: $PROJECT_ID${NC}"

# Set variables
SERVICE_NAME="hermes-backend"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build and deploy
echo -e "${BLUE}📦 Building Docker image...${NC}"
gcloud builds submit --tag $IMAGE_NAME

echo -e "${BLUE}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --set-env-vars "ALGORITHM=HS256,ACCESS_TOKEN_EXPIRE_MINUTES=30"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}🌐 Service URL: $SERVICE_URL${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Set environment variables (SECRET_KEY, GOOGLE_API_KEY, DATABASE_URL, REDIS_URL)"
echo "2. Run database migrations"
echo "3. Update Vercel with: NEXT_PUBLIC_API_URL=$SERVICE_URL"
echo ""
echo -e "${BLUE}Set environment variables with:${NC}"
echo "gcloud run services update $SERVICE_NAME --region $REGION \\"
echo "  --set-env-vars SECRET_KEY=your_secret_key,GOOGLE_API_KEY=your_api_key,DATABASE_URL=your_db_url,REDIS_URL=your_redis_url"
