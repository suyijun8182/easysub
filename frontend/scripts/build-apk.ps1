$ErrorActionPreference = 'Stop'
$frontendRoot = Split-Path $PSScriptRoot -Parent
$projectRoot = Split-Path $frontendRoot -Parent
if (-not $env:JAVA_HOME) {
    $localJdk = Get-ChildItem -LiteralPath (Join-Path $projectRoot '.android-tools/jdk') -Directory -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $localJdk) { throw 'Set JAVA_HOME to a JDK 21 installation.' }
    $env:JAVA_HOME = $localJdk.FullName
}
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android/Sdk' }
Push-Location $frontendRoot
try {
    & npm.cmd run build:android
    if ($LASTEXITCODE -ne 0) { throw 'Android web build failed.' }
    # Gradle snapshots on some Windows workspace volumes misclassify regular files.
    $stage = Join-Path $env:TEMP ('easysub-android-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $stage | Out-Null
    & robocopy.exe android (Join-Path $stage 'android') /E /XD build .gradle /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -gt 7) { throw 'Cannot stage Android sources.' }
    & robocopy.exe node_modules/@capacitor (Join-Path $stage 'node_modules/@capacitor') /E /XD build .gradle node_modules /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -gt 7) { throw 'Cannot stage Android dependencies.' }
    Push-Location (Join-Path $stage 'android')
    try {
        & .\gradlew.bat assembleDebug testDebugUnitTest --console=plain
        if ($LASTEXITCODE -ne 0) { throw 'Android APK build failed.' }
    } finally { Pop-Location }
    $apk = Join-Path $frontendRoot 'android/app/build/outputs/apk/debug/app-debug.apk'
    New-Item -ItemType Directory -Path (Split-Path $apk -Parent) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $stage 'android/app/build/outputs/apk/debug/app-debug.apk') -Destination $apk
    Write-Output $apk
} finally { Pop-Location }
