# Run this from the repo root: .\start_backend.ps1
$root = $PSScriptRoot
Set-Location $root
& "$root\fake_transfer_detector\venv\Scripts\uvicorn" backend.main:app --reload --port 8000
