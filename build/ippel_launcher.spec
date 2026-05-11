# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file para IPPEL Launcher
Gera um executável otimizado e autocontido
"""

import sys
import os

# Configurações do executável
app_name = 'IPPEL_Launcher'
main_script = 'ippel_launcher.py'

# Análise do script principal
a = Analysis(
    [main_script],
    pathex=[],
    binaries=[],
    datas=[
        # Adicionar arquivos de dados se necessário
        # ('ippel_icon.ico', '.'),  # Ícone do aplicativo
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'socket',
        'webbrowser',
        'threading',
        'subprocess',
        'time',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir módulos desnecessários para reduzir tamanho
        'PIL',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Processamento dos arquivos
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Configuração do executável
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compressão UPX para reduzir tamanho
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Não mostrar console (interface gráfica)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Configurações específicas do Windows
    # version='version_info.txt',  # Arquivo de versão (opcional) - comentado pois arquivo não existe
    # icon='ippel_icon.ico',       # Ícone do executável (opcional) - comentado pois arquivo não existe
    
    # Metadados do executável
    manifest='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity
    version="1.0.0.0"
    processorArchitecture="*"
    name="IPPEL.Launcher"
    type="win32"
  />
  <description>IPPEL RNC - Launcher de Acesso Rápido</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges xmlns="urn:schemas-microsoft-com:asm.v3">
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 e 11 -->
      <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/>
      <!-- Windows 8.1 -->
      <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/>
      <!-- Windows 8 -->
      <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/>
      <!-- Windows 7 -->
      <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/>
    </application>
  </compatibility>
</assembly>''',
)