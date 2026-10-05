param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
$repositoryPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $repositoryPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create .venv and install backend/requirements-dev.txt first.' }
if (-not $SkipBuild) {
    Push-Location (Join-Path $repositoryPath 'frontend')
    try {
        $npmCliPath = Join-Path (Split-Path (Get-Command node).Source) 'node_modules\npm\bin\npm-cli.js'
        if (Test-Path -LiteralPath $npmCliPath) { & node $npmCliPath run build } else { & npm run build }
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
}
Push-Location (Join-Path $repositoryPath 'backend')
try {
    New-Item -ItemType Directory -Force 'data' | Out-Null
    & $pythonPath -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Migration failed.' }
    $workerProcess = Start-Process -FilePath $pythonPath -ArgumentList @('-m','papergraph.worker') -WorkingDirectory (Get-Location).Path -WindowStyle Hidden -PassThru
    try { & $pythonPath -m uvicorn papergraph.api:app --host 127.0.0.1 --port 8000 --no-access-log }
    finally { if (-not $workerProcess.HasExited) { Stop-Process -Id $workerProcess.Id } }
} finally { Pop-Location }
