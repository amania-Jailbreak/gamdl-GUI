# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['E:/Python/gamdl-gui/main.py'],
    pathex=[],
    binaries=[],
    datas=[('C:/Users/okmnj/AppData/Local/Programs/Python/Python312/Lib/site-packages/customtkinter', 'customtkinter/'), ('E:/Python/gamdl-gui/binary', 'binary/'), ('E:/Python/gamdl-gui/gamdl', 'gamdl/'), ('E:/Python/gamdl-gui/device.wvd', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='gamdl-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\okmnj\\Downloads\\gamdl-downloder.ico'],
)
