# Equivalent Windows de run_hypervisor_integration.sh
# Usage:
#   $env:GANDAL_HV_FAKE='0'
#   $env:GANDAL_HV_PASSWORD_FILE="$HOME\.gandal\xapi-password"
#   $env:GANDAL_HV_CA_FILE="$HOME\.gandal\pool-ca.pem"
#   $env:GANDAL_IT_DELAY='5'
#   $env:GANDAL_IT_SSD_GB='25'
#   .\scripts\run_hypervisor_integration.ps1 ..\gandal-hypervisor

$ErrorActionPreference = "Stop"
$CellDir = Resolve-Path $args[0]
$CellPython = if ($args.Count -ge 2) { $args[1] } else { Join-Path $CellDir ".venv\Scripts\python.exe" }
$Port = if ($env:GANDAL_IT_HYPERVISOR_PORT) { $env:GANDAL_IT_HYPERVISOR_PORT } else { "8771" }
$SdkRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Work = Join-Path $env:TEMP ("gandal-hv-it-" + [guid]::NewGuid().ToString("n"))
New-Item -ItemType Directory -Path $Work | Out-Null
$Log = Join-Path $Work "cell.log"
$TokenFile = Join-Path $Work "token"

if (($env:GANDAL_HV_POLICY) -and ($env:GANDAL_HV_POLICY -ne "sandbox")) {
    throw "Les tests d'integration n'acceptent que GANDAL_HV_POLICY=sandbox."
}

try {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, [int]$Port)
    $listener.Start(); $listener.Stop()
} catch {
    throw "Le port $Port est deja occupe ; liberez-le ou definissez GANDAL_IT_HYPERVISOR_PORT."
}

$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[Convert]::ToBase64String($bytes) | Set-Content -Path $TokenFile -NoNewline -Encoding ascii

$env:GANDAL_HV_FAKE = if ($env:GANDAL_HV_FAKE) { $env:GANDAL_HV_FAKE } else { "1" }
$env:GANDAL_HV_POLICY = "sandbox"
$env:GANDAL_HV_TOKEN_FILE = $TokenFile
$env:GANDAL_HV_HOST = "127.0.0.1"
$env:GANDAL_HV_PORT = "$Port"

$ErrLog = Join-Path $Work "cell.err"
$cellProc = Start-Process -FilePath $CellPython -ArgumentList "-m","gandal_hypervisor" `
    -WorkingDirectory $CellDir -RedirectStandardOutput $Log -RedirectStandardError $ErrLog `
    -PassThru -NoNewWindow

try {
    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        if ($cellProc.HasExited) {
            Get-Content $Log, $ErrLog -ErrorAction SilentlyContinue | Write-Host
            throw "La cellule s'est arretee au demarrage."
        }
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) {
        Get-Content $Log, $ErrLog -ErrorAction SilentlyContinue | Write-Host
        throw "La cellule n'a pas repondu sur /health."
    }
    Get-Content $Log, $ErrLog -ErrorAction SilentlyContinue | Select-Object -First 3 | Write-Host

    $env:GANDAL_IT_HYPERVISOR_ENDPOINT = "http://127.0.0.1:$Port"
    $env:GANDAL_IT_HYPERVISOR_TOKEN = Get-Content $TokenFile -Raw
    $SdkPython = Join-Path $SdkRoot ".venv\Scripts\python.exe"
    if (-not (Test-Path $SdkPython)) { $SdkPython = "py" }
    Push-Location $SdkRoot
    try {
        & $SdkPython -m pytest -q tests/integration_hypervisor
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    } finally {
        Pop-Location
    }
} finally {
    if (-not $cellProc.HasExited) {
        Stop-Process -Id $cellProc.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
    Remove-Item -Recurse -Force $Work -ErrorAction SilentlyContinue
}
