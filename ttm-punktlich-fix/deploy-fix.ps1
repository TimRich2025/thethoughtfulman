# deploy-fix.ps1  -  deployed den Punktlich-Fix in einem Befehl.
# Legt post.py, post.yml, refresh-token.yml ins Repo, committet und pusht. Kein force-push.
# Aufruf:  .\deploy-fix.ps1   (oder mit -Repo "C:\pfad\zum\repo")

param(
  [string]$Repo = "C:\Users\Tim\Desktop\Automation Studios\TheThoughtfulman\Automation\thethoughtfulman-automation"
)
$ErrorActionPreference = "Stop"
$src = $PSScriptRoot

foreach ($f in @("post.py","post.yml","refresh-token.yml")) {
  if (-not (Test-Path (Join-Path $src $f))) { Write-Host "ABBRUCH. Datei fehlt neben dem Skript: $f" -ForegroundColor Red; exit 1 }
}
if (-not (Test-Path $Repo)) { Write-Host "ABBRUCH. Repo-Pfad nicht gefunden: $Repo" -ForegroundColor Red; exit 1 }

Set-Location $Repo
git fetch origin main
git reset --hard origin/main      # sauberer Stand vom Remote, vor dem Kopieren

Copy-Item (Join-Path $src "post.py") (Join-Path $Repo "post.py") -Force
$wf = Join-Path $Repo ".github\workflows"
if (-not (Test-Path $wf)) { New-Item -ItemType Directory -Path $wf | Out-Null }
Copy-Item (Join-Path $src "post.yml")          (Join-Path $wf "post.yml") -Force
Copy-Item (Join-Path $src "refresh-token.yml") (Join-Path $wf "refresh-token.yml") -Force

git add -A
git commit -m "Punktlicher Ausloeser + 45-Min-Sperre + Token-Refresh"
try { git push origin main } catch { git pull --rebase origin main; git push origin main }

Write-Host ""
Write-Host "FERTIG. Dateien deployed und gepusht." -ForegroundColor Green
Write-Host ""
Write-Host "Es bleiben 3 Schritte die nur DU mit deinem GitHub-Login machen kannst:" -ForegroundColor Cyan
Write-Host "  1) PAT anlegen: fein granular, nur dieses Repo, Actions Read+Write und Secrets Read+Write."
Write-Host "  2) Secret GH_PAT mit diesem PAT setzen (Repo Settings, Secrets and variables, Actions)."
Write-Host "  3) cron-job.org: POST auf die Dispatch-URL alle 5 Minuten. Genaue Werte in ANLEITUNG.md."
Write-Host ""
Write-Host "Danach: Actions, Workflow post, Run workflow zum Testen." -ForegroundColor Cyan
