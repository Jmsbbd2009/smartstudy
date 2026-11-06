"""Load the private .env into a child process without putting secrets in its arguments."""
import os
import sys
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
env={**os.environ}
config=root/'.env'
if config.exists():
    for line in config.read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            key,value=line.split('=',1);env[key.strip()]=value.strip()
if len(sys.argv)<2:raise SystemExit('Usage: python scripts/run_local.py <module> [arguments], e.g. alembic upgrade head or app.bootstrap')
raise SystemExit(subprocess.run([sys.executable,'-m',*sys.argv[1:]],cwd=root/'backend',env=env).returncode)
