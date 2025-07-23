# PowerShell Build Script für Simple Invites
# Windows-kompatible Version von build.sh

Write-Host "🚀 Building Simple Invites Docker Image..." -ForegroundColor Green

# Image Tag
$IMAGE_TAG = "bassdoxxx/simple_invites:latest"

try {
    # Test der Anwendung
    Write-Host "🧪 Running tests..." -ForegroundColor Yellow
    python test_app.py
    if ($LASTEXITCODE -ne 0) {
        throw "Tests failed"
    }

    # Build des Images
    Write-Host "🔨 Building Docker image..." -ForegroundColor Yellow
    docker build -t $IMAGE_TAG .
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed"
    }

    Write-Host "✅ Docker Image built successfully: $IMAGE_TAG" -ForegroundColor Green

    # Optional: Push zum Docker Hub
    $push = Read-Host "Push to Docker Hub? (y/n)"
    if ($push -eq 'y' -or $push -eq 'Y') {
        Write-Host "📤 Pushing to Docker Hub..." -ForegroundColor Yellow
        docker push $IMAGE_TAG
        if ($LASTEXITCODE -ne 0) {
            throw "Docker push failed"
        }
        Write-Host "✅ Image pushed to Docker Hub" -ForegroundColor Green
    }

    Write-Host "🎉 Build completed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Zum Deployen auf deinem Server:" -ForegroundColor Cyan
    Write-Host "1. Kopiere die docker-compose.production.yml in deinen ffw-dockersetup Ordner" -ForegroundColor White
    Write-Host "2. Füge den simple_invites Service zu deiner docker-compose.yaml hinzu" -ForegroundColor White
    Write-Host "3. Erstelle die nötigen Ordner: mkdir -p data/simple_invites configs/simple_invites" -ForegroundColor White
    Write-Host "4. Starte mit: docker-compose up -d simple_invites" -ForegroundColor White

} catch {
    Write-Host "❌ Build failed: $_" -ForegroundColor Red
    exit 1
}
