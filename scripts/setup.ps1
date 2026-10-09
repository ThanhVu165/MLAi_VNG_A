$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$requiredVersion = (Get-Content -LiteralPath '.python-version' -Raw).Trim()
& py "-$requiredVersion" -c "import sys; assert '.'.join(map(str, sys.version_info[:2])) == '$requiredVersion'"
if ($LASTEXITCODE -ne 0) { throw "Install Python $requiredVersion and the Windows py launcher first." }
$projectPython = Join-Path (Get-Location) '.venv-bootstrap/Scripts/python.exe'
if (-not (Test-Path -LiteralPath '.venv-bootstrap')) {
    & py "-$requiredVersion" -m venv .venv-bootstrap
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Existing .venv-bootstrap is incomplete; preserve it and use a fresh checkout.' }
& $projectPython -c "import sys; assert '.'.join(map(str, sys.version_info[:2])) == '$requiredVersion'"
if ($LASTEXITCODE -ne 0) { throw 'Existing virtual environment has the wrong Python version. Preserve it and use a fresh checkout.' }
& $projectPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& $projectPython -c "import openai; print('openai OK')"
if ($LASTEXITCODE -ne 0) { throw 'OpenAI SDK import failed.' }
Write-Output 'Setup complete. Activate: .\.venv-bootstrap\Scripts\Activate.ps1'
