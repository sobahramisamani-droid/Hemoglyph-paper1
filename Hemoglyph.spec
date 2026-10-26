# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

block_cipher = None

added_files = []

# 1. QML files
if os.path.isdir('qml'):
    added_files.append(('qml', 'qml'))
for qf in Path('.').glob('*.qml'):
    added_files.append((str(qf), '.'))

# 2. Add registries and database that exist in the directory
registry_candidates = [
    'HEMOGLYPH_FEATURE_REGISTRY.json',
    'HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json',
    'HEMOGLYPH_GUIDELINE_REGISTRY.json',
    'HEMOGLYPH_FEATURE_REGISTRY.json.br',
    'HEMOGLYPH_DISEASE_GUIDELINE_REGISTRY.json.br',
    'HEMOGLYPH_GUIDELINE_REGISTRY.json.br',
    'hemoglyph.db',
]

for filename in registry_candidates:
    if os.path.exists(filename):
        added_files.append((filename, '.'))

# 3. Add .env if present
if os.path.exists('.env'):
    added_files.append(('.env', '.'))

# 4. Add Icons
for icon_name in ['app_icon.ico', 'icon.ico', 'logo.ico', 'app_icon.png', 'logo.png']:
    if os.path.exists(icon_name):
        added_files.append((icon_name, '.'))

# 5. Add embedded AI engine & models if present
if os.path.isdir('bin'):
    added_files.append(('bin', 'bin'))
if os.path.isdir('models'):
    added_files.append(('models', 'models'))

hidden_imports = [
    'PySide6.QtQuick',
    'PySide6.QtQml',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'brotli',
    'openai',
    'httpx',
    'httpcore',
    'pydantic',
    'pydantic_core',
    'annotated_types',
    'typing_extensions',
    'anyio',
    'sniffio',
    'sqlite3',
    'urllib.request',
    'urllib.error',
    'urllib.parse',
    'json',
    'math',
    'hashlib',
    'hmac',
    'difflib',
    'dataclasses',
    'threading',
    'subprocess',
    'shutil',
    'license_engine',
    'sarvis_tahlil',
    'calcu',
    'paygah_dade',
    'naam_haye_vizhegi',
    'models_scientific_references',
    'namaye_registry',
    'analyse_gidlines',
    'prdicter',
    'AI',
    'ocr',
    '_ocr_support',
    'cache_registry',
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'numpy.testing', 'IPython', 'notebook'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

app_icon = None
for candidate in ['app_icon.ico', 'icon.ico', 'logo.ico', 'hemoglyph.ico']:
    if os.path.exists(candidate):
        app_icon = candidate
        break

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Hemoglyph',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)
