#!/bin/sh

echo "Updating package list and installing dependencies…"
apt-get update && apt-get install -y curl

pip install zenml[s3]==0.74.0 requests

sleep 10

for i in $(seq 1 30); do
  if curl -f http://zenml:8080/health; then
    echo "ZenML server is ready"
    break
  fi
  echo "Waiting for ZenML server..."
  sleep 2
done

echo "Getting authentication token..."
RESPONSE=$(curl -X POST http://zenml:8080/api/v1/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$ZENML_USERNAME&password=$ZENML_PASSWORD")

TOKEN=$(echo "$RESPONSE" | python3 -c 'import sys, json; print(json.load(sys.stdin).get("access_token", ""))')

if [ -z "$TOKEN" ]; then
  echo "Failed to get authentication token"
  exit 1
fi

echo "Authentication successful"

export ZENML_STORE_API_TOKEN=$TOKEN

zenml status


echo "Creating ZenML secret for MinIO credentials..."
if ! zenml secret list | grep -q s3_secret; then
  zenml secret create s3_secret \
    --aws_access_key_id="${MINIO_ROOT_USER}" \
    --aws_secret_access_key="${MINIO_ROOT_PASSWORD}"
  echo "Created s3_secret with MinIO credentials"
else
  echo "Secret 's3_secret' already exists"
  # Update the secret to ensure it has the correct credentials
  zenml secret update s3_secret \
    --aws_access_key_id="${MINIO_ROOT_USER}" \
    --aws_secret_access_key="${MINIO_ROOT_PASSWORD}"
  echo "Updated s3_secret with current MinIO credentials"
fi

echo "Registering artifact store..."
if ! zenml artifact-store list | grep -q minio-store; then
  zenml artifact-store register minio-store -f s3 \
    --path='s3://zenml-artifacts' \
    --authentication_secret=s3_secret \
    --client_kwargs="{\"endpoint_url\":\"$ENDPOINT_URL\",\"use_ssl\":false,\"region_name\":\"$MINIO_REGION\"}"
  echo "Registered minio-store artifact store"
else
  echo "Artifact store 'minio-store' already exists"
fi

echo "Registering orchestrator..."
if ! zenml orchestrator list | grep -q local-orchestrator; then
  zenml orchestrator register local-orchestrator -f local
else
  echo "Orchestrator 'local-orchestrator' already exists"
fi

echo "Registering and activating stack..."
if ! zenml stack list | grep -q newssummarizer-stack; then
    zenml stack register newssummarizer-stack \
    -a minio-store \
    -o local-orchestrator
    echo "Registered newssummarizer-stack"
else
  echo "Stack 'newssummarizer-stack' already exists."
fi

zenml stack set newssummarizer-stack
echo "Activated newssummarizer-stack"

# Test the artifact store connection
echo "Testing artifact store connection..."
if zenml artifact-store describe minio-store; then
  echo "Artifact store configuration looks good"
else
  echo "Warning: Artifact store configuration may have issues"
fi

echo "Bootstrap completed!"
