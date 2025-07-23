#!/bin/bash
# Build Script für Simple Invites Docker Image

set -e

echo "🚀 Building Simple Invites Docker Image..."

# Image Tag
IMAGE_TAG="bassdoxxx/simple_invites:latest"

# Build des Images
docker build -t $IMAGE_TAG .

echo "✅ Docker Image built successfully: $IMAGE_TAG"

# Optional: Push zum Docker Hub (auskommentiert)
echo "📤 Pushing to Docker Hub..."
docker push $IMAGE_TAG
echo "✅ Image pushed to Docker Hub"

echo "🎉 Build completed!"
echo ""
echo "Zum Deployen auf deinem Server:"
echo "1. Kopiere die docker-compose.production.yml in deinen ffw-dockersetup Ordner"
echo "2. Füge den simple_invites Service zu deiner docker-compose.yaml hinzu"
echo "3. Erstelle die nötigen Ordner: mkdir -p data/simple_invites configs/simple_invites"
echo "4. Starte mit: docker-compose up -d simple_invites"