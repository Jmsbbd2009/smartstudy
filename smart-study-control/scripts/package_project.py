"""Package source and verified debug artifacts, excluding local state and credentials."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {
    '.git', '.gradle', '.kotlin', '.venv', '.pytest_cache', '.ruff_cache', '__pycache__',
    'node_modules', 'build', 'dist', 'uploads', 'qa-private', 'playwright-report', 'test-results-private',
}


def include(path):
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED for part in relative.parts):
        return False
    if path.name in {'.env', 'local.properties', '.DS_Store'}:
        return False
    if path.suffix in {'.pyc', '.db', '.jks'} or '.db-' in path.name:
        return False
    return path.is_file() and not path.is_symlink()


def main():
    manifest = ROOT / 'docs/FILES.md'
    manifest.touch(exist_ok=True)
    files = sorted(path for path in ROOT.rglob('*') if include(path))
    manifest.write_text('# Delivered files\n\n' + ''.join(f'- `{path.relative_to(ROOT)}`\n' for path in files))
    output = ROOT.parent / 'smart-study-control.zip'
    temporary = ROOT.parent / '.smart-study-control.zip.tmp'
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, Path(ROOT.name) / path.relative_to(ROOT))
    with zipfile.ZipFile(temporary) as archive:
        if archive.testzip() is not None:
            raise RuntimeError('Archive integrity check failed')
        required = ['README.md', 'IMPLEMENTATION_PROGRESS.md', 'docs/BOOKS_AND_AI_UZ.md',
                    'artifacts/v0.3.0/smart-study-control-debug.apk', 'backend/requirements.lock.txt',
                    'android/data/schemas/uz.smartstudy.data.StudyDatabase/2.json']
        for name in required:
            if f'{ROOT.name}/{name}' not in archive.namelist():
                raise RuntimeError(f'Missing required deliverable: {name}')
    temporary.replace(output)
    print(f'{output.name}: {len(files)} files, {output.stat().st_size} bytes; integrity verified')


if __name__ == '__main__':
    main()
