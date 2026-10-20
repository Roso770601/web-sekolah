"""Use dummy injections to prove the public artifact fails closed."""
import tempfile
import unittest
from pathlib import Path

from build_public_site import ROOT, build, manifest, permitted, validate


class PublicBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='sdn-public-build-test-')
        cls.output = Path(cls.temp.name) / 'public-site'
        cls.files = build(cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_allowlist_has_no_academic_source(self):
        names = manifest()
        self.assertNotIn('nilai/nilai.html', names)
        self.assertFalse(any(name.startswith('nilai/') for name in names))
        self.assertTrue(all(permitted(name) for name in names))

    def test_forbidden_paths(self):
        for name in ['nilai/data.json', 'nilai/New folder/data_lulus.json',
                     'data.xlsx', 'data.xls', 'convert.py', 'update.bat',
                     '.git/config', '../index.html', 'folder/../index.html',
                     'secrets.json', '.env', 'folder\\data.json']:
            with self.subTest(name=name):
                self.assertFalse(permitted(name))

    def test_manifest_cannot_authorize_academic_files(self):
        with tempfile.TemporaryDirectory(prefix='sdn-dummy-manifest-') as temp:
            root = Path(temp)
            (root / 'scripts').mkdir()
            # No academic file is created or read: reject its path first.
            (root / 'scripts/public-files.txt').write_text(
                'nilai/data.json\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Forbidden source'):
                manifest(root)

    def test_dummy_injections_are_rejected(self):
        for name in ['nilai/data.json', 'nilai/New folder/data_lulus.json',
                     'dummy.xlsx', 'dummy.py', 'dummy.bat', '.env', 'unexpected.html']:
            with self.subTest(name=name):
                file = self.output / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text('DUMMY TEST ONLY', encoding='utf-8')
                try:
                    with self.assertRaises(ValueError):
                        validate(self.output)
                finally:
                    file.unlink()

    def test_modified_public_page_is_rejected(self):
        file = self.output / 'index.html'
        original = file.read_bytes()
        try:
            file.write_text('DUMMY MODIFICATION', encoding='utf-8')
            with self.assertRaises(ValueError):
                validate(self.output)
        finally:
            file.write_bytes(original)

    def test_missing_asset_is_rejected(self):
        file = self.output / 'logo.webp'
        original = file.read_bytes()
        try:
            file.unlink()
            with self.assertRaises(ValueError):
                validate(self.output)
        finally:
            file.write_bytes(original)

    def test_notice_replaces_only_build_output(self):
        notice = (self.output / 'nilai/nilai.html').read_text(encoding='utf-8')
        self.assertIn('Layanan Nilai Belum Tersedia', notice)
        self.assertNotIn('fetch(', notice)
        self.assertNotIn('localStorage', notice)
        # Do not read or execute the source portal or any academic JSON.
        self.assertTrue((ROOT / 'nilai/nilai.html').is_file())

    def test_final_package(self):
        self.assertEqual(validate(self.output), self.files)


if __name__ == '__main__':
    unittest.main(verbosity=2)
