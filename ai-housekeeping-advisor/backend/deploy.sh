
set -e

if [ -z "$1" ]; then
  echo "Usage: ./deploy.sh PROJECT_ID [REGION]"
  echo "Example: ./deploy.sh my-project-id us-central1"
  exit 1
fi

PROJECT_ID=$1
REGION=${2:-"us-central1"}

echo "Deploying backend services to project: $PROJECT_ID in region: $REGION"

echo "Deploying Image Processor..."
cd image-processor
cp requirements-gcp.txt requirements.txt
gcloud functions deploy image-processor \
  --gen2 \
  --runtime=python39 \
  --region=$REGION \
  --source=. \
  --entry-point=image_processor \
  --trigger-http \
  --allow-unauthenticated \
  --project=$PROJECT_ID
IMAGE_PROCESSOR_URL=$(gcloud functions describe image-processor --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "Image Processor deployed at: $IMAGE_PROCESSOR_URL"

echo "Deploying Message Generator..."
cd ../message-generator
cp requirements-gcp.txt requirements.txt
gcloud functions deploy message-generator \
  --gen2 \
  --runtime=python39 \
  --region=$REGION \
  --source=. \
  --entry-point=message_generator \
  --trigger-http \
  --allow-unauthenticated \
  --project=$PROJECT_ID
MESSAGE_GENERATOR_URL=$(gcloud functions describe message-generator --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "Message Generator deployed at: $MESSAGE_GENERATOR_URL"

echo "Deploying API Gateway..."
cd ../api-gateway
cp requirements-gcp.txt requirements.txt
gcloud functions deploy api-gateway \
  --gen2 \
  --runtime=python39 \
  --region=$REGION \
  --source=. \
  --entry-point=api_gateway \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars=IMAGE_PROCESSOR_URL=$IMAGE_PROCESSOR_URL,MESSAGE_GENERATOR_URL=$MESSAGE_GENERATOR_URL \
  --project=$PROJECT_ID
API_GATEWAY_URL=$(gcloud functions describe api-gateway --gen2 --region=$REGION --project=$PROJECT_ID --format="value(serviceConfig.uri)")
echo "API Gateway deployed at: $API_GATEWAY_URL"

echo "Backend deployment completed successfully!"
echo "API Gateway URL: $API_GATEWAY_URL"
echo ""
echo "Update your frontend .env.production file with:"
echo "VITE_API_URL=$API_GATEWAY_URL"
