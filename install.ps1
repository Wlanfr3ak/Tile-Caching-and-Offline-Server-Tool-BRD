#requires -Version 5.1
# Install-Skript (Windows): prueft Python, laedt fehlende Abhaengigkeiten
# (Leaflet) nach, legt config.json aus config.example.json an.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

$LeafletVersion = '1.9.4'
$LeafletBase = "https://unpkg.com/leaflet@$LeafletVersion/dist"

Write-Host '==> Python pruefen'
$py = $null
foreach ($cmd in 'python', 'py') {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) { $py = $cmd; break }
}
if (-not $py) {
    Write-Error 'Python nicht gefunden. Bitte Python >= 3.10 installieren.'
}
& $py -c "import sys; assert sys.version_info >= (3, 10), 'Python >= 3.10 benoetigt'"
Write-Host "    $(& $py --version) gefunden (keine pip-Pakete noetig)"

Write-Host "==> Leaflet $LeafletVersion pruefen"
New-Item -ItemType Directory -Force -Path 'lib' | Out-Null
foreach ($f in 'leaflet.js', 'leaflet.css') {
    $dest = Join-Path 'lib' $f
    if (-not (Test-Path $dest) -or (Get-Item $dest).Length -eq 0) {
        Write-Host "    lade $dest ..."
        Invoke-WebRequest -Uri "$LeafletBase/$f" -OutFile $dest -UseBasicParsing
    } else {
        Write-Host "    $dest vorhanden"
    }
}

if (-not (Test-Path 'config.json')) {
    Write-Host '==> config.json aus config.example.json anlegen'
    Copy-Item 'config.example.json' 'config.json'
} else {
    Write-Host '==> config.json vorhanden, wird nicht ueberschrieben'
}

Write-Host ''
Write-Host "Fertig. Start mit:  $py serve.py   (http://localhost:8080)"
