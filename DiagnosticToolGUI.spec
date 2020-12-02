# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['DiagnosticToolGUI.py'],
             pathex=['C:\\Users\\btierra\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Python 3.7\\Log Diagnostic Tool\\DiagnosticTool'],
             binaries=[],
             datas=[],
             hiddenimports=['pkg_resources.py2_warn', 'xlsxwriter', 'pandas', 'numpy', 'tkinter'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='DiagnosticToolGUI',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False )

