"""Exercise release gating and failure recovery without touching a VPS."""
import importlib.util
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('deploy_vps', Path(__file__).with_name('deploy_vps.py'))
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)

OLD = 'a' * 40
NEW = 'b' * 40


class ReleaseTests(unittest.TestCase):
    def test_health_origin_supports_the_existing_and_new_primary_domain(self):
        for domain in ('dgm.co.ir', 'artistprofile.ir'):
            self.assertEqual(deploy.health_origin({'PUBLIC_BASE_URL': f'https://{domain}/'}),
                             f'https://{domain}')

    def test_health_origin_rejects_unapproved_or_non_origin_urls(self):
        for value in ('http://artistprofile.ir', 'https://example.org',
                      'https://artistprofile.ir.attacker.example',
                      'https://name@artistprofile.ir', 'https://artistprofile.ir:443',
                      'https://artistprofile.ir/other', 'https://artistprofile.ir/?q=1'):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                deploy.health_origin({'PUBLIC_BASE_URL': value})

    def test_https_and_asset_checks_use_the_new_primary_domain(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / 'static').mkdir()
            css = b'approved-css\n'
            (project / 'static/app.css').write_bytes(css)
            digest = hashlib.sha256(css).hexdigest()[:16]
            with patch.object(deploy, 'PROJECT', project), \
                    patch.object(deploy, 'run', side_effect=[
                        f'<link href="/static/app.css?v={digest}">',
                        json.dumps({'commit': NEW}),
                    ]) as run, \
                    patch.object(deploy.subprocess, 'run', return_value=SimpleNamespace(stdout=css)) as fetch:
                deploy.healthy(NEW, 'https://artistprofile.ir')
                self.assertEqual(run.call_args_list[0].args[-1], 'https://artistprofile.ir/')
                self.assertEqual(run.call_args_list[1].args[-1],
                                 f'https://artistprofile.ir/static/release.json?v={NEW}')
                command = fetch.call_args.args[0]
                self.assertIn('artistprofile.ir:443:127.0.0.1', command)
                self.assertEqual(command[-1], f'https://artistprofile.ir/static/app.css?v={NEW}')

    def test_marker_must_identify_exact_commit_and_tag(self):
        self.assertTrue(deploy.verified_sha(NEW, f'{NEW}\trefs/tags/site-verified/{NEW}'))
        self.assertFalse(deploy.verified_sha(NEW, f'{OLD}\trefs/tags/site-verified/{NEW}'))
        self.assertFalse(deploy.verified_sha(NEW, f'{NEW}\trefs/tags/anything'))
        self.assertFalse(deploy.verified_sha(NEW, ''))

    def test_schema_and_dependency_changes_require_manual_upgrade(self):
        self.assertTrue(deploy.needs_manual_upgrade('portfolio/migrations/0005_change.py'))
        self.assertTrue(deploy.needs_manual_upgrade('requirements.txt'))
        self.assertFalse(deploy.needs_manual_upgrade('templates/base.html\nstatic/app.css'))

    def fake_git(self, *args):
        if args == ('remote', 'get-url', 'origin'):
            return deploy.REMOTE
        if args == ('rev-parse', 'HEAD'):
            return OLD
        if args[0] == 'rev-parse':
            return NEW
        if args[0] == 'ls-remote':
            return f'{NEW}\trefs/tags/site-verified/{NEW}'
        if args[0] == 'show':
            return '--bg-charcoal: #0c0d0e;'
        return ''

    def test_unverified_commit_cannot_stop_or_change_site(self):
        def git(*args):
            return '' if args[0] == 'ls-remote' else self.fake_git(*args)
        with patch.object(deploy, 'git', side_effect=git), patch.object(deploy, 'run') as run:
            deploy.deploy()
            run.assert_not_called()

    def test_dependency_change_is_rejected_before_backup_or_stop(self):
        def git(*args):
            return 'requirements.txt' if args[0] == 'diff' else self.fake_git(*args)
        with patch.object(deploy, 'git', side_effect=git), patch.object(deploy, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'manual upgrade'):
                deploy.deploy()
            run.assert_not_called()

    def test_failed_https_check_restores_code_and_static_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / 'project'
            (project / 'staticfiles').mkdir(parents=True)
            (project / 'staticfiles/app.css').write_text('new-css')
            static = root / 'dgm-static'
            static.mkdir()
            (static / 'app.css').write_text('old-css')
            with patch.object(deploy, 'PROJECT', project), patch.object(deploy, 'STATIC', static), \
                    patch.object(deploy, 'git', side_effect=self.fake_git) as git, \
                    patch.object(deploy, 'app', return_value=''), \
                    patch.object(deploy, 'run', return_value='') as run, \
                    patch.object(deploy, 'environment', return_value={}), \
                    patch.object(deploy, 'healthy', side_effect=RuntimeError('HTTPS mismatch')):
                with self.assertRaisesRegex(RuntimeError, 'HTTPS mismatch'):
                    deploy.deploy()
                self.assertEqual((static / 'app.css').read_text(), 'old-css')
                self.assertFalse((static / 'release.json').exists())
                self.assertIn(unittest.mock.call('checkout', '--detach', OLD), git.call_args_list)
                self.assertEqual(run.call_args_list[-1],
                                 unittest.mock.call('/bin/systemctl', 'start', 'dgm-portfolio.service'))


if __name__ == '__main__':
    unittest.main()
