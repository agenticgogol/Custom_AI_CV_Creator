#!/bin/bash

set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REPO="cv-creator-enhanced"
LOCATION="us-central1"
IMAGE="cv-creator-agent-enhanced"
SERVICE_NAME="cv-creator-agent-enhanced"
VERSION="2.0.0"
GAR_TAG=$LOCATION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE:$VERSION

echo "🚀 Deploying Enhanced CV Creator Agent to Google Cloud Run..."
echo "📝 Project: $PROJECT_ID"
echo "📍 Location: $LOCATION"
echo "🏷️  Tag: $GAR_TAG"
echo "✨ Enhanced Features: Multi-LLM, ATS Scoring, Change Tracking, PDF Export"

# API keys are no longer required in environment - users configure through UI
echo "ℹ️  Note: API keys are now configured by users through the web interface"
echo "   This provides better security and flexibility for multi-LLM support"

# Create repository if it doesn't exist
echo "📦 Creating Docker repository..."
gcloud artifacts repositories create $REPO \
    --repository-format=docker \
    --location=$LOCATION \
    --description="Enhanced CV Creator Agent Docker repository" \
    --project=$PROJECT_ID 2>/dev/null || echo "Repository already exists"

# Build and push image
echo "🔨 Building Docker image..."
gcloud builds submit --tag $GAR_TAG

# Create service account if it doesn't exist
echo "👤 Setting up service account..."
gcloud iam service-accounts create cv-creator-enhanced \
    --description="Enhanced CV Creator Agent service account" \
    --display-name="CV Creator Enhanced" 2>/dev/null || echo "Service account already exists"

# Deploy to Cloud Run with enhanced configuration
echo "🚢 Deploying to Cloud Run..."

# Build minimal env vars (no API keys needed)
ENV_VARS=""
if [ -f ".env" ]; then
    # Only include non-API-key environment variables
    ENV_VARS=$(awk '!/^#/ && NF && !/^PORT=/ && !/API_KEY/ {printf "%s ", $0}' .env | sed 's/ $//')
    if [ ! -z "$ENV_VARS" ]; then
        ENV_VARS="--set-env-vars $ENV_VARS"
    fi
fi

gcloud run deploy $SERVICE_NAME \
    --image=$GAR_TAG \
    --max-instances=5 \
    --min-instances=1 \
    --allow-unauthenticated \
    --region=$LOCATION \
    --memory=4Gi \
    --cpu=2 \
    --timeout=600 \
    --concurrency=50 \
    --session-affinity \
    --service-account=cv-creator-enhanced@$PROJECT_ID.iam.gserviceaccount.com \
    $ENV_VARS \
    --quiet

echo "✅ Deployment complete!"
echo "🌐 Your Enhanced CV Creator Agent is now live!"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$LOCATION --format='value(status.url)')
echo "🔗 Service URL: $SERVICE_URL"
echo ""
echo "🆕 Enhanced Features Available:"
echo "   🤖 Multi-LLM Support (OpenAI GPT-4, Google Gemini)"
echo "   📊 ATS Compliance Scoring & Analysis"
echo "   🔍 Comprehensive Gap Analysis with Recommendations"
echo "   📝 Detailed Change Tracking & Highlighting"
echo "   💬 User Feedback Integration & Application"
echo "   📄 Multiple Export Formats (PDF, DOCX, TXT, Comparison Reports)"
echo "   🛡️  Secure API Key Configuration via Web Interface"
echo "   📋 Step-by-step Workflow with Progress Tracking"
echo ""
echo "📋 Next steps:"
echo "1. Visit $SERVICE_URL to access your Enhanced CV Creator Agent"
echo "2. Configure your preferred AI provider (OpenAI or Gemini) with your API key"
echo "3. Upload a resume and job description to test the enhanced features"
echo "4. Monitor logs with: gcloud logs tail /projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout --limit=50"
echo ""
echo "🔧 To update the deployment:"
echo "1. Make your changes to the code"
echo "2. Update VERSION in this script if needed"
echo "3. Run ./deploy.sh again"
echo ""
echo "💡 Tips for users:"
echo "   - Get OpenAI API key: https://platform.openai.com/api-keys"
echo "   - Get Google AI API key: https://aistudio.google.com/app/apikey"
echo "   - Upload high-quality PDF/DOCX resumes for best results"
echo "   - Provide complete job descriptions for accurate analysis"