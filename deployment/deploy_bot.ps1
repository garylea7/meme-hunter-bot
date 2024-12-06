# PowerShell Deployment Script for Trading Bot
Write-Host "Trading Bot Deployment Script" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green

# Check if doctl is installed
if (!(Get-Command doctl -ErrorAction SilentlyContinue)) {
    Write-Host "Installing DigitalOcean CLI (doctl)..." -ForegroundColor Yellow
    winget install --id DigitalOcean.doctl
}

# Function to check if a command succeeded
function Check-LastExitCode {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error occurred. Please contact support." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

# Prepare deployment package
Write-Host "`nPreparing deployment package..." -ForegroundColor Cyan
$deploymentPath = "trading-bot-deployment"
New-Item -ItemType Directory -Force -Path $deploymentPath | Out-Null

# Copy necessary files
Copy-Item -Path "trading-bot/*" -Destination $deploymentPath -Recurse -Force

# Create deployment archive
Compress-Archive -Path "$deploymentPath/*" -DestinationPath "trading-bot.zip" -Force

Write-Host "`nDeployment package created successfully!" -ForegroundColor Green
Write-Host "`nNext steps:"
Write-Host "1. Log into your DigitalOcean account"
Write-Host "2. Go to your droplet 'meme-tracker'"
Write-Host "3. Click on 'Access' in the left menu"
Write-Host "4. Choose 'Upload' from the top menu"
Write-Host "5. Upload the 'trading-bot.zip' file from this directory"

Write-Host "`nWould you like to proceed with the upload? (yes/no)" -ForegroundColor Yellow
$response = Read-Host

if ($response -eq "yes") {
    Write-Host "`nPlease open your DigitalOcean dashboard now."
    Write-Host "The deployment package is ready at: trading-bot.zip"
}

Write-Host "`nScript completed!" -ForegroundColor Green
