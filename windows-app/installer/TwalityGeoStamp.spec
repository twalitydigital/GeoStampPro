# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../assets', 'assets'),
        ('../Logo.ico', '.'),
        ('../LICENSE.txt', '.'),
        ('../PRIVACY.md', '.'),
        ('../THIRD_PARTY_NOTICES.md', '.'),
        ('../STORE_LISTING_DRAFT.md', '.'),
        ('../STORE_PUBLISHING_GUIDE.md', '.'),
    ],
    hiddenimports=['PIL._tkinter_finder', 'pillow_heif'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TwalityGeoStamp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='../Logo.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TwalityGeoStamp',
)
