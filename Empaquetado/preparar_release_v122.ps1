# ============================================================
# TecNet Finder v1.2.2 — Preparación de la entrega Windows
# Ejecutar desde PowerShell 7, con la aplicación cerrada.
# NO realiza git commit, push, merge ni cambios en GitHub.
# ============================================================

[CmdletBinding()]
param([switch]$SoloCopiarAvance, [switch]$ReanudarUltimaCompilacion)
if ($SoloCopiarAvance -and $ReanudarUltimaCompilacion) { throw "Selecciona solo una operacion: -SoloCopiarAvance o -ReanudarUltimaCompilacion." }
$ErrorActionPreference = 'Stop'

$raiz = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$rutaBaseReleases = Join-Path $env:LOCALAPPDATA 'TecNetFinder\Releases'  # Los ejecutables se generan fuera de OneDrive para evitar bloqueos de sincronización.
$rutaUltimaRelease = Join-Path $rutaBaseReleases 'ultima_release_1.2.2.txt'  # Permite recuperar la última entrega completa para la copia académica.
$rutaBuildTemporal = Join-Path ([System.IO.Path]::GetTempPath()) ('TecNetFinder-Build-v122-' + [guid]::NewGuid().ToString('N'))  # Aísla también los archivos temporales de PyInstaller.

if ($SoloCopiarAvance) {
    if (-not (Test-Path -LiteralPath $rutaUltimaRelease -PathType Leaf)) { throw 'Todavía no existe una release 1.2.2 completa. Ejecuta primero la compilación.' }
    $rutaSalida = (Get-Content -LiteralPath $rutaUltimaRelease -Raw).Trim()  # Recupera exclusivamente una publicación que finalizó todos los pasos.
    if (-not (Test-Path -LiteralPath $rutaSalida -PathType Container)) { throw "No se encuentra la release registrada: $rutaSalida" }
} elseif ($ReanudarUltimaCompilacion) {
    # Reutiliza solo una compilacion que efectivamente termino COLLECT y tiene su EXE.
    $compilaciones = @(Get-ChildItem -LiteralPath $rutaBaseReleases -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like 'v1.2.2-*' -and (Test-Path -LiteralPath (Join-Path $_.FullName 'TecNetFinder\TecNetFinder.exe') -PathType Leaf) } |
        Sort-Object LastWriteTime -Descending)
    if ($compilaciones.Count -eq 0) { throw 'No se encontro una compilacion v1.2.2 completa para reanudar.' }
    $rutaSalida = $compilaciones[0].FullName
    Write-Host "Reanudando EXE ya compilado: $rutaSalida" -ForegroundColor Yellow
} else {
    $nombreRelease = 'v1.2.2-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
    $rutaSalida = Join-Path $rutaBaseReleases $nombreRelease  # Nunca intenta sobrescribir una entrega anterior ni carpetas bloqueadas.
}
$directorioPrograma = Join-Path $rutaSalida 'TecNetFinder'
$rutaExe = Join-Path $directorioPrograma 'TecNetFinder.exe'
$rutaInstalador = Join-Path $rutaSalida 'Instalador\TecNet Finder 1.2.2 Setup.exe'
$portable = Join-Path $rutaSalida 'TecNet-Finder-v1.2.2-portable.zip'
$fuentes = Join-Path $rutaSalida 'TecNet-Finder-v1.2.2-codigo-fuente.zip'
$rutaAcademica = 'C:\Users\rodri\OneDrive\Archivos de Guardado\DOCUMENTOS IMPORTANTES\ROBERTO CARLOS\Instituto Tecnologico de Tepic (ITT)\7MO SEMESTRE\(1) LyAII\U1\Avance 1'

function ComprobarUltimaEjecucion([string]$etapa) {
    if ($LASTEXITCODE -ne 0) { throw "Error en $etapa (código de salida: $LASTEXITCODE). No se completará la entrega." }
}

function ComprobarVersion([string]$archivo, [string]$patron) {
    if (-not (Select-String -Path $archivo -Pattern $patron -Quiet)) { throw "La versión 1.2.2 no está configurada correctamente en: $archivo" }
}

$objetos = @( $rutaInstalador, (Join-Path $rutaSalida 'TecNet-Finder-v1.2.2-portable.zip'), (Join-Path $rutaSalida 'TecNet-Finder-v1.2.2-codigo-fuente.zip') )
$rutaSumas = Join-Path $rutaSalida 'SHA256-v1.2.2.txt'

Push-Location $raiz
try {
    if (-not $SoloCopiarAvance) {
    if (-not $ReanudarUltimaCompilacion) {
    Write-Host '1/6 Verificando archivos y versión 1.2.2...' -ForegroundColor Cyan
    ComprobarVersion '.\Motor\configuracion\version_aplicacion.py' 'VERSION_ESTABLE\s*=\s*["'']1\.2\.2["'']'
    ComprobarVersion '.\Empaquetado\TecNetFinder.iss' 'MyAppVersion\s+"1\.2\.2"'
    ComprobarVersion '.\Empaquetado\version_info.txt' "FileVersion', u'1\.2\.2'"
    if (-not (Test-Path '.\Empaquetado\TecNetFinder.spec')) { throw 'Falta la especificación original de PyInstaller.' }

    Write-Host '2/6 Ejecutando la suite de pruebas...' -ForegroundColor Cyan
    python -m pytest -q
    ComprobarUltimaEjecucion 'pytest'

    Write-Host '3/6 Construyendo el EXE con PyInstaller (modo onedir, fuera de OneDrive)...' -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $rutaSalida -Force | Out-Null  # Crea un destino limpio en el perfil local, no dentro del proyecto sincronizado.
    python -m PyInstaller --clean --noconfirm --distpath $rutaSalida --workpath $rutaBuildTemporal '.\Empaquetado\TecNetFinder.spec'
    ComprobarUltimaEjecucion 'PyInstaller'
    if (-not (Test-Path -LiteralPath $rutaExe -PathType Leaf)) { throw "No se generó el EXE esperado: $rutaExe" }

    } else {
        if (-not (Test-Path -LiteralPath $rutaExe -PathType Leaf)) { throw "Falta EXE para reanudar: $rutaExe" }
        Write-Host '1-3/6 Reutilizando EXE previamente construido; no se recompila.' -ForegroundColor Cyan
    }

    Write-Host '4/6 Buscando Inno Setup 6 o 7 y generando el instalador...' -ForegroundColor Cyan
    $innoRutas = @(
        "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 7\ISCC.exe",
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 7\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )
    $iscc = $innoRutas | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) } | Select-Object -First 1
    if (-not $iscc) {
        $comando = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($comando) { $iscc = $comando.Source }
    }
    if (-not $iscc) {
        foreach ($clave in @('HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup*', 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup*', 'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup*')) {
            foreach ($registro in @(Get-ItemProperty -Path $clave -ErrorAction SilentlyContinue)) {
                if (-not $registro.InstallLocation) { continue }
                $candidato = Join-Path $registro.InstallLocation 'ISCC.exe'
                if (Test-Path -LiteralPath $candidato -PathType Leaf) { $iscc = $candidato; break }
            }
            if ($iscc) { break }
        }
    }
    if (-not $iscc) { throw 'No se encontro ISCC.exe de Inno Setup 6 ni 7. Instala Inno Setup desde jrsoftware.org o comprueba su ubicacion.' }
    Write-Host "Compilador Inno encontrado: $iscc" -ForegroundColor Green
    $carpetaInstalador = Join-Path $rutaSalida 'Instalador'  # Conserva el instalador fuera de OneDrive durante su construcción.
    & $iscc "/DMyAppFilesDir=$directorioPrograma" "/DMyAppOutputDir=$carpetaInstalador" (Join-Path $raiz 'Empaquetado\TecNetFinder.iss')  # Redirige origen y salida de Inno Setup sin alterar el icono ni el script original.
    ComprobarUltimaEjecucion 'Inno Setup'
    if (-not (Test-Path -LiteralPath $rutaInstalador -PathType Leaf)) { throw "No se generó el instalador esperado: $rutaInstalador" }

    Write-Host '5/6 Creando ZIP portable y ZIP de código fuente limpio...' -ForegroundColor Cyan
    $portable = Join-Path $rutaSalida 'TecNet-Finder-v1.2.2-portable.zip'
    $fuentes = Join-Path $rutaSalida 'TecNet-Finder-v1.2.2-codigo-fuente.zip'
    Compress-Archive -LiteralPath $directorioPrograma -DestinationPath $portable -Force

    $staging = Join-Path $env:TEMP ("TecNetFinder-Entrega-" + [guid]::NewGuid().ToString('N'))
    $carpetaFuente = Join-Path $staging 'TecNet-Finder'
    try {
        New-Item -ItemType Directory -Path $carpetaFuente -Force | Out-Null
        $directorios = @('AsistenteIA','Compilador','Interfaz','Motor','Redes','Recursos','Ejemplos','Pruebas','Empaquetado','site')
        foreach ($directorio in $directorios) {
            $origen = Join-Path $raiz $directorio
            if (-not (Test-Path $origen)) { throw "Falta la carpeta fuente: $origen" }
            $destino = Join-Path $carpetaFuente $directorio
            & robocopy $origen $destino /E /R:1 /W:1 /NFL /NDL /NJH /NJS /XD __pycache__ .pytest_cache .mypy_cache /XF *.pyc *.pyo *.tmp | Out-Null
            if ($LASTEXITCODE -gt 7) { throw "Falló la copia limpia de $directorio (Robocopy: $LASTEXITCODE)" }
        }
        foreach ($archivo in @('principal.py','README.md','ROADMAP.md','requirements.txt','requirements-build.txt','pytest.ini','.gitignore')) {
            $origen = Join-Path $raiz $archivo
            if (Test-Path $origen -PathType Leaf) { Copy-Item -LiteralPath $origen -Destination $carpetaFuente }
        }
        Compress-Archive -LiteralPath $carpetaFuente -DestinationPath $fuentes -Force
    } finally {
        if (Test-Path $staging) { Remove-Item -LiteralPath $staging -Force -Recurse }
    }

    Write-Host '6/6 Creando SHA256 y, opcionalmente, entrega académica...' -ForegroundColor Cyan
    $sumas = $objetos | ForEach-Object {
        $hash = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()
        "$hash  $(Split-Path $_ -Leaf)"
    }
    $sumas | Set-Content -LiteralPath $rutaSumas -Encoding utf8
    New-Item -ItemType Directory -Path $rutaBaseReleases -Force | Out-Null
    Set-Content -LiteralPath $rutaUltimaRelease -Value $rutaSalida -Encoding utf8  # Guarda la ubicación solo cuando la release está completamente construida y verificada.
    } else {
        Write-Host 'Copiando una build existente previamente validada...' -ForegroundColor Cyan
        foreach ($archivo in $objetos) {
            if (-not (Test-Path -LiteralPath $archivo -PathType Leaf)) { throw "Falta el artefacto: $archivo" }
        }
        if (-not (Test-Path -LiteralPath $rutaSumas -PathType Leaf)) { throw "Falta el archivo SHA256: $rutaSumas" }
        $lineas = Get-Content -LiteralPath $rutaSumas
        foreach ($archivo in $objetos) {
            $hash = (Get-FileHash -LiteralPath $archivo -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($lineas -notcontains "$hash  $(Split-Path $archivo -Leaf)") { throw "No coincide el SHA256 de $archivo. Reconstruye primero la release." }
        }
    }
    if ($SoloCopiarAvance) {
        if (-not (Test-Path -LiteralPath $rutaAcademica -PathType Container)) { throw "No está disponible la carpeta académica de OneDrive: $rutaAcademica" }
        $entrega = Join-Path $rutaAcademica 'Release 1.2.2'
        if (Test-Path -LiteralPath $entrega) { throw "La carpeta Release 1.2.2 ya existe. Para proteger la evidencia previa, revisa su contenido antes de copiar otra versión." }
        New-Item -ItemType Directory -Path $entrega | Out-Null
        foreach ($archivo in @($objetos + @($rutaSumas))) { Copy-Item -LiteralPath $archivo -Destination $entrega -ErrorAction Stop }
        Write-Host "Copia académica creada: $entrega" -ForegroundColor Green
    }
    if (-not $SoloCopiarAvance) { Write-Host "Release final (fuera de OneDrive): $rutaSalida" -ForegroundColor Green; Write-Host "EXE: $rutaExe" -ForegroundColor Green }
    Write-Host "Instalador: $rutaInstalador" -ForegroundColor Green
    Write-Host "ZIP portable: $portable" -ForegroundColor Green
    Write-Host "ZIP código fuente: $fuentes" -ForegroundColor Green
    Write-Host "SHA256: $rutaSumas" -ForegroundColor Green
    if (-not $SoloCopiarAvance) { Write-Host 'Prueba ahora el EXE y el instalador antes de usar -SoloCopiarAvance y publicar.' -ForegroundColor Yellow }
} finally {
    if (Test-Path -LiteralPath $rutaBuildTemporal -PathType Container) {
        try { Remove-Item -LiteralPath $rutaBuildTemporal -Recurse -Force -ErrorAction Stop }  # Libera el espacio temporal al finalizar, incluso si falla alguna etapa.
        catch { Write-Warning "No se pudo limpiar la compilación temporal: $rutaBuildTemporal. Se puede eliminar después de cerrar PyInstaller." }
    }
    Pop-Location
}
