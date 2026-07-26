param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv/Scripts/python.exe"

if (-not (Test-Path $python)) {
    Write-Error "No se encontró la virtualenv en $python"
    exit 1
}

Set-Location $root
& $python @Args
