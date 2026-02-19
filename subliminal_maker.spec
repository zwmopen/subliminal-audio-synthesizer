# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['subliminal_maker.py'],
             pathex=['D:/AI编程/sub音频制作'],
             binaries=[],
             datas=[],
             hiddenimports=['numpy', 'scipy', 'pydub', 'tkinter'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='潜意识音频生成器',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          icon=None)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='潜意识音频生成器')
