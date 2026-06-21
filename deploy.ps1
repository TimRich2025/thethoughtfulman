# Ein-Klick-Deploy fuer TheThoughtfulman (Reels, 2x taeglich).
# Aufruf im entpackten Ordner:
#   powershell -ExecutionPolicy Bypass -File .\deploy.ps1
# Macht automatisch: Dateien hochladen, Workflow aktivieren, ersten Reel ausloesen.
# Die Secrets im Repo (IG_ACCESS_TOKEN, IG_USER_ID) bleiben unangetastet.

param([string]$RepoName = "thethoughtfulman")

function Need($c,$h){ if(-not (Get-Command $c -ErrorAction SilentlyContinue)){ Write-Host "Fehlt: $c. $h"; exit 1 } }
Need gh  "Installieren: winget install --id GitHub.cli, dann PowerShell neu oeffnen, dann gh auth login"
Need git "Installieren: winget install --id Git.Git, dann PowerShell neu oeffnen"

gh auth status 2>$null | Out-Null
if($LASTEXITCODE -ne 0){ Write-Host "Bitte zuerst anmelden mit: gh auth login"; exit 1 }

$owner = "$(gh api user --jq .login)".Trim()
if([string]::IsNullOrWhiteSpace($owner)){ Write-Host "Konnte GitHub-Benutzer nicht lesen."; exit 1 }
$full = "$owner/$RepoName"
Write-Host "Repo: $full"

Set-Location $PSScriptRoot

if(-not (Test-Path ".git")){ git init -q }
git remote remove origin 2>$null | Out-Null
git remote add origin "https://github.com/$full.git"
git add .
git -c user.email="bot@users.noreply.github.com" -c user.name="thethoughtfulman" commit -m "umstieg auf reels, 2x taeglich" 2>$null | Out-Null
git branch -M main
Write-Host "Lade hoch (kann wegen der Videos einen Moment dauern) ..."
git push -u origin main --force
if($LASTEXITCODE -ne 0){ Write-Host "Push fehlgeschlagen. Vielleicht heisst das Repo anders. Dann: powershell -ExecutionPolicy Bypass -File .\deploy.ps1 -RepoName DEIN-REPO-NAME"; exit 1 }

Start-Sleep -Seconds 5
Write-Host "Loese den ersten Lauf aus ..."
gh workflow run post.yml -R $full 2>$null
if($LASTEXITCODE -ne 0){ Write-Host "(Start per Zeitplan kommt automatisch, kein Problem.)" }

Write-Host ""
Write-Host "FERTIG."
Write-Host "reel-01 geht heute 18:00 raus, danach laeuft es zweimal taeglich von allein."
Write-Host "Kontrolle: oeffne im Browser  github.com/$full  und klick auf den Tab Actions."
