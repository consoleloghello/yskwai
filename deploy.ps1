# deploy.ps1 - One-click deploy to GitHub Pages
# Usage:
#   powershell -ExecutionPolicy Bypass -File deploy.ps1
#   powershell -ExecutionPolicy Bypass -File deploy.ps1 -Remote "git@github.com:user/repo.git"

param(
    [string]$Remote = "",
    [string]$Branch = "master",
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 1. Read config file if Remote not provided
if (-not $Remote) {
    $confFile = Join-Path $scriptDir "deploy.conf"
    if (Test-Path $confFile) {
        $conf = Get-Content $confFile -Encoding UTF8 | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' }
        foreach ($line in $conf) {
            $parts = $line -split '=', 2
            $key = $parts[0].Trim()
            $val = $parts[1].Trim()
            if ($key -eq "REMOTE") { $Remote = $val }
            if ($key -eq "BRANCH") { $Branch = $val }
        }
    }
}

# 2. Validate
if (-not $Remote) {
    Write-Host "ERROR: Remote URL not set." -ForegroundColor Red
    Write-Host "  Option 1: .\deploy.ps1 -Remote 'git@github.com:username/repo.git'"
    Write-Host "  Option 2: Set REMOTE=... in deploy.conf"
    exit 1
}

# 3. Init git if needed
$gitDir = Join-Path $scriptDir ".git"
if (-not (Test-Path $gitDir)) {
    Write-Host "> git init" -ForegroundColor Cyan
    git init
    Write-Host "> git branch -M $Branch" -ForegroundColor Cyan
    git branch -M $Branch
}

# 4. Configure remote
$currentRemote = (git remote get-url origin 2>$null) -replace '\s+', ''
if ($currentRemote) {
    if ($currentRemote -ne $Remote) {
        Write-Host "> git remote set-url origin $Remote" -ForegroundColor Cyan
        git remote set-url origin $Remote
    }
} else {
    Write-Host "> git remote add origin $Remote" -ForegroundColor Cyan
    git remote add origin $Remote
}

# 5. Pull latest to avoid conflicts
Write-Host "> git pull --rebase origin $Branch" -ForegroundColor Cyan
try { git pull --rebase origin $Branch 2>$null } catch {}

# 6. Add files
Write-Host "> git add index.html" -ForegroundColor Cyan
git add index.html

# 7. Commit
if (-not $Message) {
    $Message = "deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}
Write-Host "> git commit -m '$Message'" -ForegroundColor Cyan
$commitResult = git commit -m $Message 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host $commitResult
}

# 8. Push
Write-Host "> git push origin $Branch" -ForegroundColor Cyan
git push origin $Branch

Write-Host ""
Write-Host "Deploy done!" -ForegroundColor Green
Write-Host "GitHub Pages will auto-deploy from branch: $Branch" -ForegroundColor Yellow

