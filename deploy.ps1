# deploy.ps1 — 一键部署到 Gitee Pages
# 用法:
#   .\deploy.ps1                          使用 deploy.conf 中的配置
#   .\deploy.ps1 -Remote "git@gitee.com:user/repo.git"
#   .\deploy.ps1 -Remote "https://gitee.com/user/repo.git" -Branch master

param(
    [string]$Remote = "",
    [string]$Branch = "master",
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 1. 读取配置文件（如果参数未指定 Remote）
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

# 2. 验证必要参数
if (-not $Remote) {
    Write-Host "请设置 Gitee 仓库地址：" -ForegroundColor Yellow
    Write-Host "  方式1: .\deploy.ps1 -Remote 'git@gitee.com:username/repo.git'" -ForegroundColor Gray
    Write-Host "  方式2: 在 deploy.conf 中设置 REMOTE=git@gitee.com:username/repo.git" -ForegroundColor Gray
    exit 1
}

# 3. 初始化 Git（如果需要）
$gitDir = Join-Path $scriptDir ".git"
if (-not (Test-Path $gitDir)) {
    Write-Host "> git init" -ForegroundColor Cyan
    git init
}

# 4. 配置远程仓库
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

# 5. 添加文件
Write-Host "> git add index.html" -ForegroundColor Cyan
git add index.html

# 6. 提交
if (-not $Message) {
    $Message = "deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
}
Write-Host "> git commit -m '$Message'" -ForegroundColor Cyan
$commitResult = git commit -m $Message 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host $commitResult
}

# 7. 推送
Write-Host "> git push origin $Branch" -ForegroundColor Cyan
git push origin $Branch

Write-Host ""
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "请前往 Gitee 仓库 Settings > Pages 启用 Pages 服务（选择 $Branch 分支）。" -ForegroundColor Yellow
