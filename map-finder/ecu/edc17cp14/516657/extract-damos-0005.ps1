# Extraire uniquement le DAMOS 0005 (A2L+hex) depuis le pack 07-2015.
# Usage : brancher le NAS/USB, puis :
#   powershell -File map-finder\ecu\edc17cp14\516657\extract-damos-0005.ps1
#   powershell -File ...\extract-damos-0005.ps1 -Source "E:\DAMOS SAMMLUNG BIG 07-2015.part001.rar"

param(
  [string]$Source = ""
)

$ErrorActionPreference = "Stop"
$dest = Join-Path $PSScriptRoot "damos-similar-0005"
$folderName = "8K1907401K_0005_504886_P714_B3UN_EDC17CP14_2.41"
$zipName = "8K1907401K_0005.zip"
$7z = "C:\Program Files\7-Zip\7z.exe"
New-Item -ItemType Directory -Force -Path $dest | Out-Null

function Find-Source {
  if ($Source -and (Test-Path -LiteralPath $Source)) { return (Resolve-Path -LiteralPath $Source).Path }
  $needles = @(
    "*SAMMLUNG*part001.rar",
    "*SAMMLUNG*.rar",
    "*Org_Files_Sortiert*",
    "*$folderName*"
  )
  $roots = @(
    "D:\STEVEN\Damos-Big-Archive\Damos-Big-Archive\Org_Files_Sortiert Damos",
    "D:\STEVEN\Damos-Big-Archive",
    "C:\Users\theda\OneDrive\Bureau", "D:\", "E:\", "F:\", "G:\", "H:\"
  )
  Get-PSDrive -PSProvider FileSystem | ForEach-Object { $roots += $_.Root }
  $roots = $roots | Select-Object -Unique
  foreach ($root in $roots) {
    if (-not (Test-Path -LiteralPath $root)) { continue }
    foreach ($pat in $needles) {
      $hit = Get-ChildItem -LiteralPath $root -Filter $pat -Recurse -Depth 4 -Force -ErrorAction SilentlyContinue |
        Select-Object -First 1
      if ($hit) { return $hit.FullName }
    }
  }
  return $null
}

function Copy-UsefulFromDir([string]$dir) {
  $copied = @()
  Get-ChildItem -LiteralPath $dir -File -Force -ErrorAction SilentlyContinue | ForEach-Object {
    if ($_.Name -match '_uncleaned\.hex$') { return }
    if ($_.Extension -match '^\.(a2l|hex|odx|pdx)$') {
      Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $dest $_.Name) -Force
      $copied += $_.Name
    }
  }
  return $copied
}

$found = Find-Source
if (-not $found) {
  Write-Host "Rien trouve. Colle le dossier $folderName sur le Bureau, ou passe -Source chemin\vers\part001.rar"
  exit 1
}
Write-Host "Source : $found"

$copied = @()
if ((Test-Path -LiteralPath $found) -and ((Get-Item -LiteralPath $found).PSIsContainer)) {
  if ((Split-Path $found -Leaf) -eq $folderName) {
    $copied = Copy-UsefulFromDir $found
  } else {
    $sub = Get-ChildItem -LiteralPath $found -Directory -Recurse -Filter $folderName -ErrorAction SilentlyContinue |
      Select-Object -First 1
    if ($sub) { $copied = Copy-UsefulFromDir $sub.FullName }
    $zip = Get-ChildItem -LiteralPath $found -Recurse -Filter $zipName -ErrorAction SilentlyContinue |
      Select-Object -First 1
    if ($zip) {
      Copy-Item -LiteralPath $zip.FullName -Destination (Join-Path $dest $zipName) -Force
      $copied += $zipName
    }
  }
} elseif ($found -match '\.rar$') {
  if (-not (Test-Path -LiteralPath $7z)) { throw "7-Zip manquant : $7z" }
  $insideA2l = "DAMOS SAMMLUNG BIG 07-2015/Org_Files_Sortiert Damos/$folderName/$folderName.a2l"
  $insideHex = "DAMOS SAMMLUNG BIG 07-2015/Org_Files_Sortiert Damos/$folderName/$folderName.hex"
  $insideOdx = "DAMOS SAMMLUNG BIG 07-2015/Org_Files_Sortiert Damos/$folderName/FL_$folderName.odx"
  $insideZip = "DAMOS SAMMLUNG BIG 07-2015/Master_Eprom_Audi_ab_2.7L/150 MHz/2,7 ltr/Audi B8/0281016456_HS_VL/$zipName"
  & $7z x "-o$dest" -y -- $found $insideA2l $insideHex $insideOdx $insideZip
  Get-ChildItem -LiteralPath $dest -Recurse -File | ForEach-Object {
    if ($_.DirectoryName -ne $dest) {
      Move-Item -LiteralPath $_.FullName -Destination (Join-Path $dest $_.Name) -Force
    }
  }
  $copied = (Get-ChildItem -LiteralPath $dest -File | Where-Object { $_.Extension -match 'a2l|hex|odx|zip' }).Name
} else {
  throw "Source inconnue : $found"
}

Write-Host ""
if ($copied.Count -eq 0) {
  Write-Host "Aucun fichier utile copie."
  exit 1
}
Write-Host "Copie dans $dest :"
$copied | ForEach-Object { Write-Host "  $_" }
Write-Host ""
Write-Host "WinOLS : ouvrir ORI_FLS.fls, importer le .a2l en similar. Ne pas copier les offsets 0005."
