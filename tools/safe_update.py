#!/usr/bin/env python3
"""Run inside Kodi: RunScript(path/to/safe_update.py,ZIP_PATH,SHA256).
Backs up only this skin, preserves user files, and refuses updates during playback.
No background service; no userdata or library writes.
"""
import hashlib
import json
from pathlib import PurePosixPath
import os
import shutil
import stat
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

ADDON = 'skin.arctic.fuse.3.ko'


def validate_package(path, expected_sha256):
    with open(path, 'rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else hashlib.sha256(f.read()).hexdigest()
    if digest != expected_sha256.lower():
        raise ValueError('Package SHA256 mismatch')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate package paths')
        if sum(i.file_size for i in z.infolist()) > 256 * 1024 * 1024:
            raise ValueError('Package too large')
        for i in z.infolist():
            p = PurePosixPath(i.filename)
            if p.is_absolute() or '..' in p.parts or '\\' in i.filename or not p.parts or p.parts[0] != ADDON:
                raise ValueError('Unsafe package path')
            if stat.S_ISLNK(i.external_attr >> 16):
                raise ValueError('Package symlinks not allowed')
        metadata = ET.fromstring(z.read(ADDON + '/addon.xml'))
        if metadata.get('id') != ADDON:
            raise ValueError('Wrong skin ID')
        font = ET.fromstring(z.read(ADDON + '/1080i/Font.xml'))
        if font.find("fontset[@id='Apple SD Gothic Neo']") is None:
            raise ValueError('Personal font option missing')
        if z.testzip() is not None:
            raise ValueError('Package CRC error')
    return metadata


def main():
    import xbmc
    import xbmcvfs
    if len(sys.argv) != 3:
        raise ValueError('Expected ZIP_PATH and SHA256')
    package = xbmcvfs.translatePath(sys.argv[1])
    meta = validate_package(package, sys.argv[2])
    if xbmc.Player().isPlaying():
        raise RuntimeError('Stop playback before updating the skin')
    skin = xbmcvfs.translatePath('special://home/addons/' + ADDON)
    personal = xbmcvfs.translatePath('special://home/media/Fonts/')
    for weight in ('Regular', 'Bold'):
        if not os.path.isfile(personal + 'AppleSDGothicNeo-' + weight + '.ttf'):
            raise RuntimeError('Personal font missing; restore it before updating')
    root = xbmcvfs.translatePath('special://profile/skin-update-backups/')
    os.makedirs(root, exist_ok=True)
    backup = os.path.join(root, time.strftime('%Y%m%d-%H%M%S') + '-' + str(time.time_ns()))
    shutil.copytree(skin, backup)
    staging = skin + '.update-staging'
    if os.path.exists(staging):
        raise RuntimeError('Staging directory already exists; inspect prior update')
    shutil.copytree(skin, staging)
    try:
        with zipfile.ZipFile(package) as z:
            for i in z.infolist():
                relative = PurePosixPath(i.filename).parts[1:]
                if not relative or i.is_dir():
                    continue
                dest = os.path.join(staging, *relative)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with z.open(i) as source, open(dest, 'wb') as target:
                    shutil.copyfileobj(source, target)
        # All replacement files are prepared before touching the installed skin.
        for current, _, files in os.walk(staging):
            for name in files:
                src = os.path.join(current, name)
                dst = os.path.join(skin, os.path.relpath(src, staging))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                os.replace(src, dst)
        xbmc.executebuiltin('UpdateLocalAddons', True)
        xbmc.executebuiltin('ReloadSkin()')
        with open(os.path.join(root, 'last-update.json'), 'w') as f:
            json.dump({'version': meta.get('version'), 'backup': backup, 'sha256': sys.argv[2], 'status': 'files_applied'}, f)
    except Exception:
        # Recover pre-update files; keep backup for manual inspection.
        for current, _, files in os.walk(backup):
            for name in files:
                src = os.path.join(current, name)
                dst = os.path.join(skin, os.path.relpath(src, backup))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
        xbmc.executebuiltin('ReloadSkin()')
        raise
    finally:
        shutil.rmtree(staging)


if __name__ == '__main__':
    main()
