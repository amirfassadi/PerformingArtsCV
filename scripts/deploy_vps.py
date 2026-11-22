#!/usr/bin/python3
"""Root-installed, pull-based deployment for this VPS. Never execute repo code as root."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

PROJECT = Path('/home/amir/performingartscv')
STATIC = Path('/var/www/dgm-static')
BRANCH = 'codex/restore-artistic-design'
REMOTE = 'https://github.com/amirfassadi/PerformingArtsCV.git'
PYTHON = str(PROJECT / '.venv/bin/python')


def run(*args, env=None):
    result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=180)
    if result.returncode:
        # Command arguments never contain credentials; application output is kept
        # in the root-readable service journal for diagnosing failed deployments.
        raise RuntimeError(f'{args[0]} exited {result.returncode}: {result.stderr[-4000:]}')
    return result.stdout.strip()


def app(*args, env=None):
    return run('/usr/sbin/runuser', '-u', 'amir', '--preserve-environment',
               '--', *map(str, args), env=env)


def git(*args):
    return app('/usr/bin/git', '-C', PROJECT, *args)


def verified_sha(sha, remote_output):
    """Only a lightweight marker for this exact commit can authorize deployment."""
    return remote_output.splitlines() == [f'{sha}\trefs/tags/site-verified/{sha}']


def needs_manual_upgrade(changed):
    return any(name.startswith('portfolio/migrations/') or
               Path(name).name.startswith('requirements')
               for name in changed.splitlines())


def environment():
    result = os.environ.copy()
    for line in Path('/etc/dgm-portfolio.env').read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, value = line.split('=', 1)
        if not re.fullmatch(r'[A-Z][A-Z0-9_]*', key):
            raise RuntimeError('Unexpected environment file format')
        result[key] = value
    result['PYTHONDONTWRITEBYTECODE'] = '1'
    return result


def remove_stage(path):
    if path.parent != STATIC.parent or not path.name.startswith('.dgm-static-') or path.is_symlink():
        raise RuntimeError('Refusing to remove an unexpected static directory')
    if path.exists():
        shutil.rmtree(path)


def stage_static(sha):
    source = PROJECT / 'staticfiles'
    if source.is_symlink() or any(p.is_symlink() for p in source.rglob('*')):
        raise RuntimeError('Static output must not contain symbolic links')
    stage = Path(tempfile.mkdtemp(prefix='.dgm-static-', dir=STATIC.parent))
    try:
        shutil.copytree(source, stage, dirs_exist_ok=True)
        (stage / 'release.json').write_text(json.dumps({'commit': sha, 'theme': 'charcoal-crimson'}))
        stage.chmod(0o755)
        for item in stage.rglob('*'):
            item.chmod(0o755 if item.is_dir() else 0o644)
        return stage
    except BaseException:
        remove_stage(stage)
        raise


def healthy(sha):
    base = ['/usr/bin/curl', '--fail', '--silent', '--show-error',
            '--max-time', '15', '--retry', '5', '--retry-connrefused',
            '--retry-delay', '1', '--resolve', 'dgm.co.ir:443:127.0.0.1']
    html = run(*base, 'https://dgm.co.ir/')
    expected = (PROJECT / 'static/app.css').read_bytes()
    # Compare actual downloaded bytes; text-mode conversion must not hide a mismatch.
    response = subprocess.run([*base, f'https://dgm.co.ir/static/app.css?v={sha}'],
                              check=True, capture_output=True, timeout=120).stdout
    if response != expected:
        raise RuntimeError('Nginx is serving CSS from a different release')
    digest = hashlib.sha256(expected).hexdigest()[:16]
    if f'app.css?v={digest}' not in html:
        raise RuntimeError('Homepage is not using this release asset fingerprint')
    release = json.loads(run(*base, f'https://dgm.co.ir/static/release.json?v={sha}'))
    if release.get('commit') != sha:
        raise RuntimeError('Public release identity does not match the tested commit')


def deploy(check_only=False):
    if git('remote', 'get-url', 'origin') != REMOTE:
        raise RuntimeError('Unexpected repository origin')
    if git('status', '--porcelain'):
        raise RuntimeError('Server checkout has uncommitted changes; refusing to overwrite them')
    git('fetch', '--no-tags', 'origin',
        f'+refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}')
    target = git('rev-parse', f'origin/{BRANCH}')
    if not re.fullmatch(r'[0-9a-f]{40}', target):
        raise RuntimeError('Invalid target SHA')
    marker = git('ls-remote', '--refs', 'origin', f'refs/tags/site-verified/{target}')
    if not verified_sha(target, marker):
        print(f'WAIT: {target} has not passed production CI. Site left unchanged.')
        return
    previous = git('rev-parse', 'HEAD')
    if previous == target:
        print(f'Already deployed: {target}')
        return
    changed = git('diff', '--name-only', previous, target, '--',
                  'requirements*.txt', 'portfolio/migrations/')
    if needs_manual_upgrade(changed):
        raise RuntimeError('Dependency/schema changes require a reviewed manual upgrade')
    if '--bg-charcoal: #0c0d0e;' not in git('show', f'{target}:static/app.css'):
        raise RuntimeError('The approved charcoal design is missing')
    if check_only:
        print(f'READY: {previous} -> {target}; no files or services changed.')
        return

    env = environment()
    print(run('/bin/systemctl', 'start', 'dgm-backup.service'))
    git('update-ref', 'refs/dgm/previous', previous)
    previous_static = Path(tempfile.mkdtemp(prefix='.dgm-static-previous-', dir=STATIC.parent))
    previous_static.rmdir()  # Reserve a unique name for the rename below.
    stage = None
    swapped = False
    stopped = False
    try:
        run('/bin/systemctl', 'stop', 'dgm-portfolio.service')
        stopped = True
        git('checkout', '--detach', target)
        print(app(PYTHON, PROJECT / 'manage.py', 'check', '--deploy', env=env))
        print(app(PYTHON, PROJECT / 'manage.py', 'collectstatic', '--clear', '--noinput', env=env))
        stage = stage_static(target)
        if not STATIC.is_dir() or STATIC.is_symlink():
            raise RuntimeError('Unexpected public static directory')
        STATIC.rename(previous_static)
        try:
            stage.rename(STATIC)
        except BaseException:
            previous_static.rename(STATIC)
            raise
        swapped = True
        run('/bin/systemctl', 'start', 'dgm-portfolio.service')
        healthy(target)
    except BaseException:
        if stopped:
            run('/bin/systemctl', 'stop', 'dgm-portfolio.service')
            git('checkout', '--detach', previous)
            if swapped:
                failed = Path(tempfile.mkdtemp(prefix='.dgm-static-failed-', dir=STATIC.parent))
                failed.rmdir()
                STATIC.rename(failed)
                previous_static.rename(STATIC)
                remove_stage(failed)
            run('/bin/systemctl', 'start', 'dgm-portfolio.service')
        print(f'Deployment failed; restored previous code and public CSS: {previous}')
        raise
    finally:
        if stage is not None and stage.exists():
            remove_stage(stage)
    remove_stage(previous_static)
    print(f'DEPLOYED and HTTPS/CSS verified: {target}')


if __name__ == '__main__':
    import fcntl
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate the candidate without deploying it')
    options = parser.parse_args()
    if os.geteuid() != 0:
        parser.error('Install and run this script as root; application commands run as amir')
    with open('/run/dgm-deploy.lock', 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        deploy(options.check)
