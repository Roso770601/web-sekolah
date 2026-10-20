"""Offline tests only: no real school requests, no student source data."""
import hashlib
import unittest
from check_deployment import ACADEMIC_PATHS, DOMAIN, verify_once


class DeploymentCheckTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.home = b'<html>Dummy school homepage</html>'
        self.sha = hashlib.sha256(self.home).hexdigest()

    def transport(self, path, method):
        self.calls.append((path, method))
        if path in ACADEMIC_PATHS:
            self.assertEqual(method, 'HEAD')
            return 404, b''
        if path == '/':
            return 200, self.home
        if path == '/nilai/nilai.html':
            return 200, b'Layanan Nilai Belum Tersedia'
        if path == '/CNAME':
            return 200, DOMAIN.encode()
        return 200, b''

    def test_success_and_academic_head_only(self):
        verify_once(self.sha, self.transport)
        for path in ACADEMIC_PATHS:
            self.assertEqual([method for url, method in self.calls if url == path], ['HEAD'])

    def test_exposed_academic_path_fails_before_reading_homepage(self):
        def exposed(path, method):
            self.calls.append((path, method))
            return 200, b''
        with self.assertRaisesRegex(ValueError, 'Academic URL'):
            verify_once(self.sha, exposed)
        self.assertEqual(self.calls, [(ACADEMIC_PATHS[0], 'HEAD')])

    def test_redirect_does_not_count_as_blocked(self):
        with self.assertRaisesRegex(ValueError, 'Academic URL'):
            verify_once(self.sha, lambda path, method: (302, b''))

    def test_wrong_homepage_fails(self):
        with self.assertRaisesRegex(ValueError, 'Homepage revision'):
            verify_once('0' * 64, self.transport)

    def test_wrong_domain_fails(self):
        def transport(path, method):
            return (200, b'dummy.invalid') if path == '/CNAME' else self.transport(path, method)
        with self.assertRaisesRegex(ValueError, 'Custom domain'):
            verify_once(self.sha, transport)

    def test_missing_public_asset_fails(self):
        def transport(path, method):
            return (404, b'') if path == '/logo.webp' else self.transport(path, method)
        with self.assertRaisesRegex(ValueError, 'required public'):
            verify_once(self.sha, transport)


if __name__ == '__main__':
    unittest.main(verbosity=2)
