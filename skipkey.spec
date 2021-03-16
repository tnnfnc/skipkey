# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['skipkey.py'],
             pathex=['..\\skipkey', 'C:\\Python\\skipkey\\skipkey'],
             binaries=[('..\\share\\sdl2\\bin\\libpng16-16.dll', '.')],
             datas=[('..\\skipkey\\*.json', '.'), ('..\\skipkey\\locale\\it\\LC_MESSAGES\\*', 'locale\\it\\LC_MESSAGES\\.'), ('..\\skipkey\\data\\icons\\*', 'data\\icons\\.'), ('..\\skipkey\\data\\*.*', 'data\\.'), ('..\\skipkey\\kv\\*', 'kv\\.'), ('..\\skipkey\\*.kv', '.')],
             hiddenimports=['win32timezone', 'pynput.keyboard._win32', 'pynput.mouse._win32'],
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
          [],
          exclude_binaries=True,
          name='skipkey',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='..\\skipkey\\data\\icons\\skip_big.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='skipkey')
