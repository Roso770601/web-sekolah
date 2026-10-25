"""Offline regression tests: load function definitions only, never the BAT menu.

Git is simulated in a temporary directory except for one local staging test.
No school repository mutation, credentials, network, commits or pushes.
"""
import base64
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which('powershell.exe')
REAL_GIT = shutil.which('git')


@unittest.skipUnless(os.name == 'nt' and POWERSHELL, 'Windows PowerShell 5.1 required')
class UpdateGitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sdn-update-git-')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        payload = (ROOT / 'update.bat').read_text(encoding='utf-8').split(
            '# POWERSHELL_PAYLOAD\n', 1)[1]
        self.definitions = payload.split('\n$project = ', 1)[0]
        self.env = os.environ.copy()
        self.env['PATH'] = str(self.work) + os.pathsep + self.env['PATH']
        self.env['SDN_TEST_PYTHON'] = sys.executable
        (self.work / 'git.cmd').write_text(
            '@echo off\n"%SDN_TEST_PYTHON%" "%~dp0fake_git.py" %*\n'
            'exit /b %errorlevel%\n', encoding='ascii')
        (self.work / 'fake_git.py').write_text(
            'import os, sys\n'
            'if "credential" in sys.argv:\n'
            '    data = sys.stdin.read()\n'
            '    assert "protocol=https" in data and "host=github.com" in data\n'
            'print(os.environ.get("SDN_TEST_STDOUT", ""), end="")\n'
            'print(os.environ.get("SDN_TEST_STDERR", ""), end="", file=sys.stderr)\n'
            'sys.exit(int(os.environ.get("SDN_TEST_EXIT", "0")))\n', encoding='ascii')

    def run_ps(self, body, *, stdout='', stderr='', code=0, real_git=False):
        env = self.env.copy()
        env.update(SDN_TEST_STDOUT=stdout, SDN_TEST_STDERR=stderr,
                   SDN_TEST_EXIT=str(code))
        if real_git:
            env['PATH'] = os.environ['PATH']
        script = "$ProgressPreference = 'SilentlyContinue'\n" + self.definitions + '\ntry {\n' + body + '''
            if ($ErrorActionPreference -ne 'Stop') { throw 'Preference leaked' }
        } catch { [Console]::Error.WriteLine($_.Exception.Message); exit 1 }
        '''
        encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
        return subprocess.run(
            [POWERSHELL, '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
            cwd=self.work, env=env, capture_output=True, text=True, timeout=30)

    def test_warning_exit_zero_returns_only_stdout_under_stop(self):
        result = self.run_ps(
            "$out = @(Git-Checked -GitArgs @('diff','--name-only')); "
            "if ($out.Count -ne 1 -or $out[0] -cne 'index.html') { throw 'Polluted stdout' }; "
            "Write-Output 'OK'",
            stdout='index.html\n',
            stderr="warning: in the working copy of 'index.html', LF will be replaced by CRLF the next time Git touches it\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'OK')
        self.assertEqual(result.stderr, '')

    def test_windows_powershell_stop_reproduces_legacy_stderr_failure(self):
        result = self.run_ps("""
            $caught = $false
            try { $null = @(& git -c core.quotepath=false diff 2>$null) } catch {
                $caught = $true
                if ($_.FullyQualifiedErrorId -notmatch 'NativeCommandError') { throw }
                if ($_.Exception.Message -notmatch 'LF will be replaced by CRLF') { throw }
            }
            if (-not $caught) { throw 'Legacy failure was not reproduced' }
        """, stderr="warning: LF will be replaced by CRLF\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_failure_with_stderr_uses_exit_code_and_hides_diagnostics(self):
        result = self.run_ps("Git-Checked -GitArgs @('fetch','origin'); Write-Output 'UNSAFE'",
                             stderr='private diagnostic: dummy-sensitive-value\n', code=128)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('exit code 128', result.stderr)
        self.assertNotIn('dummy-sensitive-value', result.stdout + result.stderr)
        self.assertNotIn('UNSAFE', result.stdout)

    def test_failure_without_stderr_still_stops_and_restores_preference(self):
        result = self.run_ps("""
            $caught = $false
            try { Git-Checked -GitArgs @('diff') } catch {
                $caught = $true
                if ($_.Exception.Message -notmatch 'exit code 7') { throw }
                if ($ErrorActionPreference -ne 'Stop') { throw 'Preference leaked on failure' }
            }
            if (-not $caught) { throw 'Nonzero exit ignored' }
        """, code=7)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_credential_stdin_and_stdout_remain_separate_from_warning(self):
        result = self.run_ps('''
            $lines = @(Git-Checked -GitArgs @('credential','fill') -InputText "protocol=https`nhost=github.com`n`n")
            if ($lines.Count -ne 2 -or $lines[1] -cne 'password=dummy-test-value') { throw 'Credential output corrupted' }
        ''', stdout='username=test\npassword=dummy-test-value\n', stderr='helper warning\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('dummy-test-value', result.stdout + result.stderr)

    def test_credential_failure_blocks_before_any_api_call(self):
        result = self.run_ps("""
            function Invoke-RestMethod { throw 'API must not be called' }
            Assert-PagesSettings
            Write-Output 'UNSAFE'
        """, stderr='helper failure\n', code=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Autentikasi GitHub diperlukan', result.stderr)
        self.assertNotIn('API must not be called', result.stderr)
        self.assertNotIn('UNSAFE', result.stdout)

    @unittest.skipUnless(REAL_GIT, 'Git required')
    def test_real_git_lf_warning_in_disposable_repo(self):
        repo = self.work / 'repo'
        subprocess.run([REAL_GIT, 'init', '-q', str(repo)], check=True, capture_output=True)
        page = repo / 'index.html'
        page.write_bytes(b'<html>Disposable LF fixture</html>\n')
        # Confirm this Git installation actually emits the reported warning.
        args = ['-C', str(repo), '-c', 'core.autocrlf=true', '-c', 'core.safecrlf=warn',
                'add', '--', 'index.html']
        probe = subprocess.run([REAL_GIT, *args], capture_output=True, text=True, check=True)
        self.assertIn('LF will be replaced by CRLF', probe.stderr)
        page.write_bytes(b'<html>Changed disposable LF fixture</html>\n')
        result = self.run_ps("""
            $out = @(Git-Checked -GitArgs @('-C','repo','-c','core.autocrlf=true','-c','core.safecrlf=warn','add','--','index.html'))
            if ($out.Count -ne 0) { throw 'Warning leaked into stdout' }
        """, real_git=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertEqual(page.read_bytes(), b'<html>Changed disposable LF fixture</html>\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
