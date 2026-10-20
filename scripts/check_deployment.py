"""Post-deployment checks. Academic endpoints receive HEAD only, never GET.

Not invoked by local builds or preview workflows. It is run only after a
successful authorized deployment, or deliberately by the operator.
"""
import argparse
import hashlib
import re
import time
import urllib.error
import urllib.request

DOMAIN = 'sdn1sukamanah.my.id'
BASE = 'https://' + DOMAIN
PUBLIC_PATHS = [
    '/ppdb.html', '/daftar.html', '/verifikasi.html',
    '/login.html', '/login_portal_akademik.html', '/CCTV.html',
    '/berita.html', '/galeri.html', '/profil.html', '/profil-guru.html',
    '/kurikulum.html', '/logo.webp', '/gambar-sekolah.webp',
    '/galeri/upacara.webp', '/login.css', '/style.css',
    '/dokumen/kurikulum/kurikulum-sdn1-sukamanah-2026-2027.pdf',
]
ACADEMIC_PATHS = ['/nilai/data.json', '/nilai/New%20folder/data_lulus.json']


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request(path, method='HEAD'):
    # All URLs are fixed public school paths; never follow an external redirect.
    req = urllib.request.Request(BASE + path, method=method, headers={
        'User-Agent': 'SDN1Sukamanah-PostDeployment-Check',
        'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache',
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=15) as response:
            body = response.read(2_000_001) if method == 'GET' else b''
            if len(body) > 2_000_000:
                raise ValueError('Public response exceeds verification limit')
            return response.status, body
    except urllib.error.HTTPError as error:
        # Do not read error bodies, particularly for academic endpoints.
        status = error.code
        error.close()
        return status, b''


def verify_once(expected_sha, transport=request):
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha):
        raise ValueError('Invalid expected homepage checksum')
    # Check restrictions first. A 200 response is a failure even if it is a
    # generic HTML fallback. No academic response body is ever requested.
    for path in ACADEMIC_PATHS:
        status, _ = transport(path, 'HEAD')
        if status not in {404, 410}:
            raise ValueError('Academic URL is not confirmed unavailable (HEAD only)')
    status, homepage = transport('/', 'GET')
    if status != 200 or hashlib.sha256(homepage).hexdigest() != expected_sha:
        raise ValueError('Homepage revision does not match the deployed artifact')
    status, notice = transport('/nilai/nilai.html', 'GET')
    if status != 200 or b'Layanan Nilai Belum Tersedia' not in notice:
        raise ValueError('Grades availability notice is missing')
    status, cname = transport('/CNAME', 'GET')
    if status != 200 or cname.decode('ascii').strip() != DOMAIN:
        raise ValueError('Custom domain file does not match')
    for path in PUBLIC_PATHS:
        status, _ = transport(path, 'HEAD')
        if status != 200:
            raise ValueError('A required public page or asset is unavailable')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-index-sha', required=True)
    parser.add_argument('--attempts', type=int, default=6)
    parser.add_argument('--delay', type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.attempts <= 6 or not 0 <= args.delay <= 30:
        parser.error('Invalid retry limits')
    for attempt in range(args.attempts):
        try:
            verify_once(args.expected_index_sha)
            print('PASS: HTTPS domain, homepage revision, public assets, notice, and academic URL restrictions.')
            break
        except (ValueError, OSError) as error:
            if attempt == args.attempts - 1:
                raise SystemExit('FAIL: post-deployment verification. ' + str(error))
            time.sleep(args.delay)
