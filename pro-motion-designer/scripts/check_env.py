"""Check (and explain how to install) everything the studio needs.

  python check_env.py            # report
  python check_env.py --json     # machine-readable

Prints one line per dependency and, for anything missing, the install command for this OS.
It never installs anything itself: run the printed commands (system package managers may
need the user's OK).
"""
import importlib.util
import json
import platform
import shutil
import subprocess
import sys

OS = platform.system()  # 'Windows' | 'Darwin' | 'Linux'


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20, shell=isinstance(cmd, str))
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else ''
    except Exception:
        return None


def install_hint(name):
    hints = {
        'node': {'Windows': 'winget install OpenJS.NodeJS.LTS', 'Darwin': 'brew install node', 'Linux': 'sudo apt install nodejs npm  (or use nvm)'},
        'ffmpeg': {'Windows': 'winget install Gyan.FFmpeg', 'Darwin': 'brew install ffmpeg', 'Linux': 'sudo apt install ffmpeg'},
        'python-pkgs': {k: f'{sys.executable} -m pip install --user numpy pillow matplotlib' for k in ('Windows', 'Darwin', 'Linux')},
        'playwright': {k: 'npm install   (in the project folder)  then  npx playwright install chromium' for k in ('Windows', 'Darwin', 'Linux')},
    }
    return hints[name].get(OS, hints[name]['Linux'])


def main():
    rows = []
    node = shutil.which('node')
    rows.append(('node >= 18', bool(node), run(['node', '-v']) if node else None, install_hint('node')))
    npm = shutil.which('npm') or shutil.which('npm.cmd')
    rows.append(('npm', bool(npm), run('npm -v') if npm else None, install_hint('node')))
    rows.append((f'python >= 3.9', sys.version_info >= (3, 9), sys.version.split()[0], 'install Python 3.9+ from python.org'))
    missing = [m for m in ('numpy', 'PIL', 'matplotlib') if importlib.util.find_spec(m) is None]
    rows.append(('numpy, pillow, matplotlib', not missing, 'ok' if not missing else 'missing: ' + ', '.join(missing), install_hint('python-pkgs')))
    ff = shutil.which('ffmpeg')
    rows.append(('ffmpeg + ffprobe', bool(ff and shutil.which('ffprobe')), run(['ffmpeg', '-version']) if ff else None, install_hint('ffmpeg')))
    pw = run('npx --no-install playwright --version') if npm else None
    rows.append(('playwright + chromium (per project)', bool(pw and 'Version' in pw), pw, install_hint('playwright')))

    if '--json' in sys.argv:
        print(json.dumps([{'dep': d, 'ok': ok, 'found': f, 'install': h} for d, ok, f, h in rows], indent=1))
        return
    print(f'OS: {OS} {platform.release()} - python: {sys.executable}')
    for d, ok, f, h in rows:
        print(f"  {'OK  ' if ok else 'MISS'}  {d:<38} {f or ''}")
        if not ok:
            print(f'        install: {h}')
    if OS == 'Windows':
        print('\nWindows notes: run Python with PYTHONIOENCODING=utf8 if you print non-ASCII; ffmpeg on Windows has no glob input, use the sheet.py helper for contact sheets.')


if __name__ == '__main__':
    main()
