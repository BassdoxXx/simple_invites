#!/bin/bash
# Build script for Docker image with proper static file handling

echo "Building Docker image for simple_invites..."

# Build the Docker image
docker build -t bassdoxxx/simple_invites:latest .

# Show the image info
docker image ls bassdoxxx/simple_invites:latest

echo ""
echo "Image built successfully."
echo ""

# Ask if the image should be pushed
read -p "Do you want to push the image to Docker Hub? (y/n): " push_answer
if [[ $push_answer == "y" || $push_answer == "Y" ]]; then
  echo "Pushing image to Docker Hub..."
  docker push bassdoxxx/simple_invites:latest
fi