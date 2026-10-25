@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 exit /b 1
set "SDN_UPDATE_SCRIPT=%~f0"
set "SDN_UPDATE_MODE=%~1"
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; try { $raw=[IO.File]::ReadAllText($env:SDN_UPDATE_SCRIPT); $parts=$raw -split '\r?\n# POWERSHELL_PAYLOAD\r?\n',2; if($parts.Count -ne 2){throw 'Payload tidak ditemukan'}; & ([scriptblock]::Create($parts[1])) } catch { Write-Host 'Pembaruan dihentikan:' $_.Exception.Message; exit 1 }"
set "SDN_UPDATE_RESULT=%ERRORLEVEL%"
if /i "%SDN_UPDATE_MODE%"=="--check" exit /b %SDN_UPDATE_RESULT%
echo.
pause
exit /b %SDN_UPDATE_RESULT%
# POWERSHELL_PAYLOAD
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Git-Checked {
    param([string[]]$GitArgs, [string]$InputText)
    $git = Get-Command git -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $previousErrorAction = $ErrorActionPreference
    try {
        # Windows PowerShell 5.1 can turn native stderr into a terminating
        # NativeCommandError under Stop, even with 2>$null and exit code 0.
        # Keep stderr private (credential helpers may include sensitive data),
        # return stdout only, and decide success from the captured exit code.
        $ErrorActionPreference = 'Continue'
        if ($PSBoundParameters.ContainsKey('InputText')) {
            $result = @($InputText | & $git.Source -c core.quotepath=false @GitArgs 2>$null)
        } else {
            $result = @(& $git.Source -c core.quotepath=false @GitArgs 2>$null)
        }
        $gitExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousErrorAction
    }
    if ($gitExitCode -ne 0) { throw ('Git gagal pada langkah ' + $GitArgs[0] + ' (exit code ' + $gitExitCode + '). Tidak dilanjutkan; periksa autentikasi/status Git secara manual.') }
    return $result
}
function Assert-SafeName {
    param([string]$Name)
    if ($Name -notmatch '^[A-Za-z0-9 _./()-]+$' -or $Name -match '(^|/)(\.|\.\.|nilai)(/|$)' -or $Name -match '(^|/)\.' -or
        $Name -match '(?i)\.(xlsx?|xlsm|xlsb|csv|py|bat|cmd|ps1|pem|key|pfx|p12|env|bak|zip|7z)$' -or
        $Name -match '(?i)(^|/)[^/]*(credential|secret|password|token)[^/]*$' -or
        ($Name -match '(?i)\.json$' -and $Name -cne 'berita/data.json')) {
        throw ('Berkas sensitif atau jalur tidak aman ditolak: ' + $Name)
    }
}
function Read-PublicAllowlist {
    param([string]$Project)
    $list = Join-Path $Project 'scripts\public-files.txt'
    if (-not (Test-Path -LiteralPath $list -PathType Leaf)) { throw 'Daftar izin publik tidak tersedia.' }
    $names = @([IO.File]::ReadAllLines($list) | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith('#') })
    if ($names.Count -eq 0 -or @($names | Sort-Object -Unique).Count -ne $names.Count) { throw 'Daftar izin kosong atau duplikat.' }
    foreach ($name in $names) { Assert-SafeName $name }
    return $names
}
function Assert-PublicPaths {
    param([string[]]$Names, [string[]]$Allowed)
    foreach ($name in $Names) {
        Assert-SafeName $name
        if ($Allowed -cnotcontains $name) { throw ('Di luar daftar izin publik: ' + $name + '. Gunakan PR terpisah untuk perubahan alat/workflow/daftar izin.') }
    }
}
function Assert-NoSecrets {
    param([string]$Text, [string]$Label)
    $patterns = @(
        '-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----',
        'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}',
        '\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
        '(?i)\bBearer\s+[A-Za-z0-9._-]{20,}',
        '(?i)https?://[^\s/@:]+:[^\s/@]+@',
        '(?i)\b(?:api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*["''][A-Za-z0-9_./+\-=]{8,}["'']'
    )
    foreach ($pattern in $patterns) {
        if ($Text -match $pattern) { throw ('Pola kredensial ditemukan pada ' + $Label + '. Nilainya tidak ditampilkan; publikasi diblokir.') }
    }
}
function Assert-PublicFileContents {
    param([string]$Project, [string[]]$Names)
    foreach ($name in $Names) {
        $file = Join-Path $Project $name
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw ('Penghapusan/rename tidak didukung pembaruan rutin: ' + $name) }
        $item = Get-Item -LiteralPath $file -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('Symlink ditolak: ' + $name) }
        $item = $item.Directory
        while ($item.FullName -ne $Project) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw ('Symlink/junction ditolak: ' + $name) }
            $item = $item.Parent
            if ($null -eq $item) { throw 'Jalur keluar dari proyek.' }
        }
        if ([IO.Path]::GetExtension($name) -match '^\.(html|css|js|json|xml|txt)$' -or $name -ceq 'CNAME') {
            Assert-NoSecrets ([IO.File]::ReadAllText($file)) $name
        }
    }
}
function Get-PublicChanges {
    param([string[]]$Allowed)
    if (@(Git-Checked -GitArgs @('diff','--cached','--name-only')).Count -gt 0) { throw 'Staging sudah terisi. Tinjau/unstage melalui VS Code terlebih dahulu; skrip tidak mereset staging.' }
    $names = @(@(Git-Checked -GitArgs @('diff','--name-only','HEAD')) + @(Git-Checked -GitArgs @('ls-files','--others','--exclude-standard')) | Sort-Object -Unique)
    Assert-PublicPaths $names $Allowed
    return $names
}
function Get-OutgoingPaths {
    param([string[]]$Allowed)
    # Routine publication accepts linear commits only; merge resolution needs PR review.
    if (@(Git-Checked -GitArgs @('rev-list','--min-parents=2','origin/main..HEAD')).Count -gt 0) { throw 'Ada merge commit lokal yang belum dipush. Gunakan PR/review terpisah; publikasi rutin diblokir.' }
    # Inspect every outgoing commit, not just the final net diff.
    $names = @(Git-Checked -GitArgs @('log','--format=','--name-only','origin/main..HEAD') | Where-Object { $_ } | Sort-Object -Unique)
    Assert-PublicPaths $names $Allowed
    if ($names.Count -gt 0) {
        $patch = @(Git-Checked -GitArgs (@('log','--format=','-p','origin/main..HEAD','--') + $names))
        $added = ($patch | Where-Object { $_.StartsWith('+') -and -not $_.StartsWith('+++') }) -join "`n"
        Assert-NoSecrets $added 'commit yang belum dipush'
    }
    return $names
}
function Assert-MainAndSync {
    $branch = (Git-Checked -GitArgs @('branch','--show-current')) -join ''
    if ($branch -cne 'main') { throw 'Publikasi rutin hanya dari main. Pilih/sinkronkan main sendiri; skrip tidak berpindah branch atau merge.' }
    foreach ($state in @('MERGE_HEAD','rebase-merge','rebase-apply','CHERRY_PICK_HEAD','REVERT_HEAD')) {
        $statePath = (Git-Checked -GitArgs @('rev-parse','--git-path',$state)) -join ''
        if (Test-Path -LiteralPath $statePath) { throw 'Ada operasi Git belum selesai.' }
    }
    foreach ($argsList in @(@('remote','get-url','origin'),@('remote','get-url','--push','origin'))) {
        $url = (Git-Checked -GitArgs $argsList) -join ''
        if ($url -cnotin @('https://github.com/Roso770601/web-sekolah.git','https://github.com/Roso770601/web-sekolah','git@github.com:Roso770601/web-sekolah.git')) { throw 'Remote origin/push bukan repository sekolah yang disetujui.' }
    }
    $null = Git-Checked -GitArgs @('rev-parse','--verify','origin/main')
    $countText = (Git-Checked -GitArgs @('rev-list','--left-right','--count','origin/main...HEAD')) -join ''
    $counts = @($countText.Trim() -split '\s+')
    if ($counts.Count -ne 2 -or [int]$counts[0] -gt 0) { throw 'main tertinggal atau divergen dari origin/main. Sinkronkan secara manual di VS Code; tidak ada merge/reset otomatis.' }
}
function Assert-PagesSettings {
    # Credential is consumed in memory only. Do not print it or write it to disk.
    $env:GIT_TERMINAL_PROMPT = '0'
    $env:GCM_INTERACTIVE = 'never'
    try {
        $lines = @(Git-Checked -GitArgs @('credential','fill') -InputText "protocol=https`nhost=github.com`n`n")
    } catch { throw 'Autentikasi GitHub diperlukan. Selesaikan login GitHub di VS Code terlebih dahulu.' }
    $credentials = @{}
    foreach ($line in $lines) {
        $pair = $line -split '=',2
        if ($pair.Count -eq 2) { $credentials[$pair[0]] = $pair[1] }
    }
    if (-not $credentials.ContainsKey('password')) { throw 'Autentikasi API GitHub tidak tersedia.' }
    $headers = @{Authorization=('Bearer ' + $credentials['password']); Accept='application/vnd.github+json'; 'User-Agent'='SDN1Sukamanah-Update-Preflight'}
    $base = 'https://api.github.com/repos/Roso770601/web-sekolah'
    try {
        $pages = Invoke-RestMethod -Uri ($base + '/pages') -Headers $headers -TimeoutSec 30
        $environment = Invoke-RestMethod -Uri ($base + '/environments/github-pages') -Headers $headers -TimeoutSec 30
        $policy = Invoke-RestMethod -Uri ($base + '/environments/github-pages/deployment-branch-policies') -Headers $headers -TimeoutSec 30
        Assert-PagesResponse $pages $environment $policy
    } catch { throw 'Pengaturan Pages/HTTPS/environment tidak sesuai atau tidak dapat diverifikasi. Publikasi diblokir; periksa GitHub melalui akun pengelola.' }
    finally { $headers.Clear(); $credentials.Clear(); $lines = $null }
}
function Assert-PagesResponse {
    param($Pages, $Environment, $Policy)
    $rules = @($Policy.branch_policies)
    if ($Pages.build_type -cne 'workflow' -or $Pages.cname -cne 'sdn1sukamanah.my.id' -or $Pages.https_enforced -ne $true -or
        $Environment.deployment_branch_policy.custom_branch_policies -ne $true -or $rules.Count -ne 1 -or
        $rules[0].name -cne 'main' -or $rules[0].type -cne 'branch') { throw 'Konfigurasi publikasi tidak sesuai.' }
}
function Test-PublicBuild {
    param([string]$Project)
    $python = Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1
    $work = Join-Path ([IO.Path]::GetTempPath()) ('sdn-routine-preview-' + [guid]::NewGuid().ToString('N'))
    $output = Join-Path $work 'public-site'
    # Build reads only allowlisted public sources; never run the Excel converter here.
    & $python.Source (Join-Path $Project 'scripts\build_public_site.py') --output $output *> $null
    if ($LASTEXITCODE -ne 0) { throw ('Build publik gagal. Tidak ada commit/push. Periksa builder secara manual. Folder uji: ' + $work) }
    & $python.Source (Join-Path $Project 'scripts\build_public_site.py') --check-only --output $output *> $null
    if ($LASTEXITCODE -ne 0) { throw 'Validasi akhir paket gagal.' }
    Write-Host ('Paket publik tervalidasi (lokal): ' + $output)
}

$project = [IO.Path]::GetFullPath((Split-Path -Parent $env:SDN_UPDATE_SCRIPT)).TrimEnd('\')
Set-Location -LiteralPath $project
$root = (Git-Checked -GitArgs @('rev-parse','--show-toplevel')) -join ''
if ([IO.Path]::GetFullPath($root).TrimEnd('\') -ne $project) { throw 'BAT harus berada di root proyek.' }
Assert-MainAndSync
$allowed = @(Read-PublicAllowlist $project)
Write-Host '========================================'
Write-Host 'PEMBARUAN WEBSITE SDN 1 SUKAMANAH - MAIN'
Write-Host '1. Publikasikan perubahan website publik'
Write-Host '2. Update Data Nilai (persiapan lokal saja)'
Write-Host '3. Batal / Keluar'
Write-Host '4. Periksa saja (tanpa commit/push/konversi)'
if ($env:SDN_UPDATE_MODE -eq '--check') { $choice = '4' }
elseif ($env:SDN_UPDATE_MODE) { throw 'Argumen tidak dikenali. Gunakan --check atau tanpa argumen.' }
else { $choice = Read-Host 'Pilih 1, 2, 3, atau 4' }
if ($choice -eq '3') { Write-Host 'Dibatalkan.'; exit 0 }
if ($choice -notin @('1','2','4')) { throw 'Pilihan tidak valid.' }
if ($choice -eq '2') {
    $status = @(Git-Checked -GitArgs @('status','--porcelain'))
    if ($status.Count -gt 0) { throw 'Persiapan nilai memerlukan working tree bersih. Tidak ada data lama yang diubah.' }
    $excel = Join-Path $project 'nilai\data_siswa.xlsx'
    $converter = Join-Path $project 'convert_excel_to_json.py'
    if (-not (Test-Path -LiteralPath $excel -PathType Leaf)) { throw 'Excel sumber tidak tersedia.' }
    if (-not (Test-Path -LiteralPath $converter -PathType Leaf)) { throw 'Konverter tidak tersedia.' }
    $python = Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1
    Write-Host 'Mode LOKAL: menyalin Excel dan konverter ke folder persiapan terpisah.'
    Write-Host 'Tidak menimpa JSON lama; tidak menjalankan staging, commit, fetch, atau push.'
    Write-Host 'Folder hasil dapat berisi data sensitif. Jangan unggah atau bagikan folder ini.'
    if ((Read-Host 'Ketik SIAPKAN untuk melanjutkan') -cne 'SIAPKAN') { Write-Host 'Dibatalkan.'; exit 0 }
    $localRoot = [Environment]::GetFolderPath('LocalApplicationData')
    if ([string]::IsNullOrWhiteSpace($localRoot)) { throw 'Folder lokal pengguna tidak tersedia.' }
    $work = Join-Path $localRoot ('SDN1Sukamanah\PersiapanNilai\' + [guid]::NewGuid().ToString('N'))
    $projectFull = [IO.Path]::GetFullPath($project).TrimEnd('\') + '\'
    if ([IO.Path]::GetFullPath($work).StartsWith($projectFull,[StringComparison]::OrdinalIgnoreCase)) { throw 'Folder persiapan tidak boleh berada di repository.' }
    $null = New-Item -ItemType Directory -Path (Join-Path $work 'nilai')
    Write-Host ('Folder persiapan: ' + $work)
    Copy-Item -LiteralPath $converter -Destination (Join-Path $work 'convert_excel_to_json.py')
    Copy-Item -LiteralPath $excel -Destination (Join-Path $work 'nilai\data_siswa.xlsx')
    & $python.Source (Join-Path $work 'convert_excel_to_json.py') *> $null
    if ($LASTEXITCODE -ne 0) { throw 'Konversi Python gagal. Folder persiapan dipertahankan; data sumber tidak diubah.' }
    if (-not (Test-Path -LiteralPath (Join-Path $work 'nilai\data.json') -PathType Leaf)) { throw 'Konverter tidak menghasilkan JSON.' }
    $after = @(Git-Checked -GitArgs @('status','--porcelain'))
    if ($after.Count -gt 0) { throw 'Status proyek berubah selama persiapan. Tinjau secara manual; tidak ada publikasi.' }
    Write-Host ('Selesai. JSON lokal: ' + (Join-Path $work 'nilai\data.json'))
    Write-Host 'Tidak ada commit atau push. JSON proyek lama tetap utuh.'
    exit 0
}


$changed = @(Get-PublicChanges $allowed)
$outgoing = @(Get-OutgoingPaths $allowed)
$all = @($changed + $outgoing | Sort-Object -Unique)
Assert-PublicFileContents $project $all
Write-Host 'Perubahan lokal yang akan di-commit:'
if ($changed.Count -eq 0) { Write-Host ' (tidak ada)' } else { $changed | ForEach-Object { Write-Host (' - ' + $_) } }
Write-Host 'Berkas dalam commit lokal yang belum dipush:'
if ($outgoing.Count -eq 0) { Write-Host ' (tidak ada)' } else { $outgoing | ForEach-Object { Write-Host (' - ' + $_) } }
if ($choice -eq '4') {
    Write-Host 'PEMERIKSAAN SAJA SELESAI. Tidak ada fetch, staging, commit, push, atau konversi.'
    Write-Host 'Sinkronisasi memakai snapshot origin/main lokal. Pengaturan GitHub belum diperiksa; ini bukan izin publikasi.'
    exit 0
}
Write-Host 'Memperbarui informasi origin/main; tidak ada pull atau merge otomatis.'
$null = Git-Checked -GitArgs @('fetch','origin','refs/heads/main:refs/remotes/origin/main')
Assert-MainAndSync
$outgoing = @(Get-OutgoingPaths $allowed)
$base = (Git-Checked -GitArgs @('rev-parse','origin/main')) -join ''
if ($changed.Count -eq 0 -and $outgoing.Count -eq 0) { Write-Host 'Tidak ada perubahan untuk dipublikasikan.'; exit 0 }
Assert-PagesSettings
Test-PublicBuild $project
if ($changed.Count -gt 0) {
    Write-Host 'Commit akan menyertakan SELURUH versi file berikut di disk:'
    $changed | ForEach-Object { Write-Host (' - ' + $_) }
    Write-Host 'File baru di luar daftar izin, penghapusan, alat/workflow, dan data akademik memerlukan PR terpisah.'
    if ((Read-Host 'Ketik COMMIT untuk menyimpan perubahan lokal; lainnya batal') -cne 'COMMIT') { Write-Host 'Dibatalkan.'; exit 0 }
    $now = @(Get-PublicChanges $allowed)
    if (@(Compare-Object $changed $now).Count -gt 0) { throw 'Daftar perubahan berubah; ulangi pemeriksaan.' }
    Assert-PublicFileContents $project $now
    Test-PublicBuild $project
    $null = Git-Checked -GitArgs (@('add','--') + $now)
    $staged = @(Git-Checked -GitArgs @('diff','--cached','--name-only'))
    if (@(Compare-Object $now $staged).Count -gt 0) { throw 'Staging tidak sesuai; tinjau secara manual.' }
    Assert-PublicPaths $staged $allowed
    $null = Git-Checked -GitArgs @('diff','--cached','--check')
    $patch = @(Git-Checked -GitArgs @('diff','--cached'))
    Assert-NoSecrets (($patch | Where-Object { $_.StartsWith('+') -and -not $_.StartsWith('+++') }) -join "`n") 'staged diff'
    $null = Git-Checked -GitArgs @('commit','-m','Perbarui website publik SDN 1 Sukamanah')
    Write-Host 'Commit lokal selesai.'
}
if (@(Git-Checked -GitArgs @('status','--porcelain')).Count -gt 0) { throw 'Working tree berubah; push dibatalkan.' }
$outgoing = @(Get-OutgoingPaths $allowed)
$head = (Git-Checked -GitArgs @('rev-parse','HEAD')) -join ''
Write-Host 'Berkas dalam SEMUA commit yang akan dipush:'
$outgoing | ForEach-Object { Write-Host (' - ' + $_) }
Write-Host ('Commit terbaru: ' + $head)
Write-Host 'Tujuan: origin/main. Push akan memicu build dan deployment GitHub Pages resmi.'
Write-Host 'JSON akademik lama tidak disertakan dalam paket Pages dan tidak boleh berubah pada commit baru.'
if ((Read-Host 'Ketik PUBLIKASIKAN MAIN untuk push; lainnya batal') -cne 'PUBLIKASIKAN MAIN') { Write-Host 'Push dibatalkan. Commit lokal tetap tersimpan.'; exit 0 }
$null = Git-Checked -GitArgs @('fetch','origin','refs/heads/main:refs/remotes/origin/main')
if (((Git-Checked -GitArgs @('rev-parse','origin/main')) -join '') -ne $base) { throw 'origin/main berubah sejak pemeriksaan. Push dibatalkan; sinkronkan secara manual.' }
Assert-MainAndSync
if (((Git-Checked -GitArgs @('rev-parse','HEAD')) -join '') -ne $head -or @(Git-Checked -GitArgs @('status','--porcelain')).Count -gt 0) { throw 'Commit/file berubah; ulangi pemeriksaan.' }
$null = Get-OutgoingPaths $allowed
Assert-PagesSettings
$null = Git-Checked -GitArgs @('push','origin','refs/heads/main:refs/heads/main')
Write-Host 'Push main berhasil. Ini BELUM membuktikan deployment berhasil.'
Write-Host 'Pantau build, deploy, dan verify: https://github.com/Roso770601/web-sekolah/actions'
