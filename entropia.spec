# -*- mode: python ; coding: utf-8 -*-
#
# Spec do PyInstaller para gerar o cliente Entropia como .exe unico.
#
# Build:
#     venv\Scripts\pyinstaller.exe entropia.spec --clean --noconfirm
#
# Saida: dist\Entropia.exe
#
# O app.json do repositorio e embutido como template. Na primeira
# execucao do .exe, persistencia.py copia esse template para o lado
# do executavel (onde ele pode ser editado / escrito).

block_cipher = None


a = Analysis(
    ['entropia.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.json', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'flask',
        'gunicorn',
        'bcrypt',
        'werkzeug',
        'jinja2',
        'click',
        'itsdangerous',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Entropia',
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
)
