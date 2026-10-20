@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 exit /b 1
set "SDN_UPDATE_SCRIPT=%~f0"
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; try { $raw=[IO.File]::ReadAllText($env:SDN_UPDATE_SCRIPT); $parts=$raw -split '\r?\n# POWERSHELL_PAYLOAD\r?\n',2; if($parts.Count -ne 2){throw 'Payload tidak ditemukan'}; & ([scriptblock]::Create($parts[1])) } catch { Write-Host 'Pembaruan dihentikan:' $_.Exception.Message; exit 1 }"
set "SDN_UPDATE_RESULT=%ERRORLEVEL%"
echo.
pause
exit /b %SDN_UPDATE_RESULT%
# POWERSHELL_PAYLOAD
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Git-Checked {
    param([string[]]$GitArgs)
    $result = @(& git @GitArgs 2>$null)
    if ($LASTEXITCODE -ne 0) { throw ('Perintah Git gagal: ' + $GitArgs[0] + '. Periksa Git secara manual; proses tidak dilanjutkan.') }
    return $result
}
function Assert-OnlyHomepageChanges {
    $staged = @(Git-Checked -GitArgs @('diff','--cached','--name-only'))
    if ($staged.Count -gt 0) { throw 'Staging sudah berisi perubahan. Tinjau dan selesaikan staging secara manual terlebih dahulu.' }
    $changed = @(Git-Checked -GitArgs @('diff','--name-only'))
    $untracked = @(Git-Checked -GitArgs @('ls-files','--others','--exclude-standard'))
    $other = @($changed + $untracked | Where-Object { $_ -ne 'index.html' })
    if ($other.Count -gt 0) {
        Write-Host 'Ada file di luar pilihan tampilan:'
        $other | ForEach-Object { Write-Host (' - ' + $_) }
        throw 'Tidak ada staging, commit, atau push yang dilakukan. Selesaikan perubahan lain secara manual.'
    }
    if (-not (Test-Path -LiteralPath 'index.html' -PathType Leaf)) { throw 'index.html tidak tersedia.' }
    $tracked = @(Git-Checked -GitArgs @('ls-files','--','index.html'))
    if ($tracked.Count -ne 1) { throw 'index.html harus sudah terlacak Git.' }
    return $changed
}

$project = Split-Path -Parent $env:SDN_UPDATE_SCRIPT
Set-Location -LiteralPath $project
$root = (Git-Checked -GitArgs @('rev-parse','--show-toplevel')) -join ''
if ([IO.Path]::GetFullPath($root).TrimEnd('\') -ne [IO.Path]::GetFullPath($project).TrimEnd('\')) { throw 'BAT harus berada di root proyek Git.' }
$branch = (Git-Checked -GitArgs @('branch','--show-current')) -join ''
if ([string]::IsNullOrWhiteSpace($branch)) { throw 'Detached HEAD: pilih branch terlebih dahulu.' }
Write-Host '========================================'
Write-Host 'PEMBARUAN WEBSITE SDN 1 SUKAMANAH'
Write-Host ('Branch aktif: ' + $branch)
Write-Host '========================================'
Write-Host '1. Update Tampilan Website'
Write-Host '2. Update Data Nilai (persiapan lokal)'
Write-Host '3. Batal / Keluar'
$choice = Read-Host 'Pilih 1, 2, atau 3'
if ($choice -eq '3') { Write-Host 'Dibatalkan. Tidak ada perubahan.'; exit 0 }
if ($choice -notin @('1','2')) { throw 'Pilihan tidak valid.' }
if ($branch -ne 'perbaikan-tampilan-mobile') { throw 'Gunakan branch perbaikan-tampilan-mobile. Skrip tidak berpindah branch atau menggabungkan main.' }
$null = Git-Checked -GitArgs @('status','--porcelain')
$operation = @(Git-Checked -GitArgs @('rev-parse','--git-path','MERGE_HEAD'))
if (Test-Path -LiteralPath ($operation -join '')) { throw 'Ada merge yang belum selesai.' }
foreach ($state in @('rebase-merge','rebase-apply','CHERRY_PICK_HEAD','REVERT_HEAD')) {
    $statePath = (Git-Checked -GitArgs @('rev-parse','--git-path',$state)) -join ''
    if (Test-Path -LiteralPath $statePath) { throw 'Ada operasi Git yang belum selesai.' }
}

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

Write-Host 'Pilihan file tampilan yang diizinkan pada tahap ini:'
Write-Host '1. index.html (beranda saja)'
if ((Read-Host 'Pilih file: ketik 1; lainnya batal') -ne '1') { Write-Host 'Dibatalkan.'; exit 0 }
$changed = @(Assert-OnlyHomepageChanges)
$null = Git-Checked -GitArgs @('diff','--check','--','index.html')
if ($changed.Count -gt 0) {
    Write-Host 'File yang akan di-commit: index.html'
    if ((Read-Host 'Ketik COMMIT untuk membuat commit lokal') -cne 'COMMIT') { Write-Host 'Dibatalkan.'; exit 0 }
    $null = Assert-OnlyHomepageChanges
    $null = Git-Checked -GitArgs @('add','--','index.html')
    $staged = @(Git-Checked -GitArgs @('diff','--cached','--name-only'))
    if ($staged.Count -ne 1 -or $staged[0] -ne 'index.html') { throw 'Staged diff tidak sesuai; hentikan dan tinjau staging secara manual.' }
    $null = Git-Checked -GitArgs @('diff','--cached','--check')
    $null = Git-Checked -GitArgs @('commit','-m','Perbaiki tampilan responsif beranda SDN 1 Sukamanah','--','index.html')
    Write-Host 'Commit lokal selesai.'
} else { Write-Host 'Tidak ada perubahan lokal baru. Akan memeriksa commit yang belum dipush.' }
if (@(Git-Checked -GitArgs @('status','--porcelain')).Count -gt 0) { throw 'Working tree tidak bersih; push dibatalkan.' }
# Jangan menganggap dataset aman hanya karena disebut dummy. Periksa nama, bukan isinya.
$academic = @(Git-Checked -GitArgs @('ls-files','--','nilai/*.json','nilai/**/*.json','*.xlsx'))
if ($academic.Count -gt 0) {
    Write-Host 'PUSH DIBLOKIR: berkas akademik masih terlacak Git:'
    $academic | ForEach-Object { Write-Host (' - ' + $_) }
    throw 'Keamanan publikasi akademik belum terverifikasi. Commit lokal tetap tersimpan. Jangan menghapus data secara sembarangan.'
}
Write-Host 'Pastikan pemicu Pages/workflow pada GitHub telah diperiksa dan branch ini tidak menerbitkan produksi.'
if ((Read-Host 'Ketik SUDAH DIPERIKSA untuk mengonfirmasi pemeriksaan pengelola') -cne 'SUDAH DIPERIKSA') { Write-Host 'Push dibatalkan.'; exit 0 }
# Fetch tidak menggabungkan branch atau mengubah file kerja.
$null = Git-Checked -GitArgs @('fetch','origin','main')
$remoteBranch = @(Git-Checked -GitArgs @('ls-remote','--heads','origin',('refs/heads/' + $branch)))
$base = 'refs/remotes/origin/main'
if ($remoteBranch.Count -gt 0) {
    $null = Git-Checked -GitArgs @('fetch','origin',$branch)
    $base = 'refs/remotes/origin/' + $branch
}
$null = Git-Checked -GitArgs @('merge-base','--is-ancestor',$base,'HEAD')
$outgoing = @(Git-Checked -GitArgs @('log','--format=','--name-only',($base + '..HEAD')) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Sort-Object -Unique)
if (@($outgoing | Where-Object { $_ -ne 'index.html' }).Count -gt 0) { throw 'Commit yang belum dipush memuat file selain index.html. Push diblokir.' }
if ($outgoing.Count -eq 0) { Write-Host 'Tidak ada commit tampilan untuk dipush.'; exit 0 }
Write-Host 'File dalam commit yang akan dipush: index.html'
Write-Host ('Tujuan: origin / ' + $branch + '. Bukan main; tidak ada merge otomatis.')
$head = (Git-Checked -GitArgs @('rev-parse','HEAD')) -join ''
Write-Host ('Commit: ' + $head)
if ((Read-Host ('Ketik PUSH ' + $branch + ' untuk melanjutkan')) -cne ('PUSH ' + $branch)) { Write-Host 'Push dibatalkan. Commit lokal tetap ada.'; exit 0 }
if (((Git-Checked -GitArgs @('branch','--show-current')) -join '') -ne $branch) { throw 'Branch berubah; push dibatalkan.' }
if (((Git-Checked -GitArgs @('rev-parse','HEAD')) -join '') -ne $head) { throw 'Commit berubah; push dibatalkan.' }
if (@(Git-Checked -GitArgs @('status','--porcelain')).Count -gt 0) { throw 'Ada perubahan baru; push dibatalkan.' }
$null = Git-Checked -GitArgs @('push','origin',('HEAD:refs/heads/' + $branch))
Write-Host 'Push branch pengembangan selesai. Tidak ada merge ke main yang dijalankan skrip.'
