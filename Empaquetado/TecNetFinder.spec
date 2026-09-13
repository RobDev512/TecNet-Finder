# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

raiz_proyecto = Path(SPECPATH).resolve().parent

datos = [
    (str(raiz_proyecto / "Recursos"), "Recursos"),
    (str(raiz_proyecto / "Ejemplos"), "Ejemplos"),
]

analisis = Analysis(
    [str(raiz_proyecto / "principal.py")],
    pathex=[str(raiz_proyecto)],
    binaries=[],
    datas=datos,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

python_empaquetado = PYZ(analisis.pure)

ejecutable = EXE(
    python_empaquetado,
    analisis.scripts,
    [],
    exclude_binaries=True,
    name="TecNetFinder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(raiz_proyecto / "Recursos" / "LogoTNF.ico"),
    version=str(raiz_proyecto / "Empaquetado" / "version_info.txt"),
)

distribucion = COLLECT(
    ejecutable,
    analisis.binaries,
    analisis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TecNetFinder",
)