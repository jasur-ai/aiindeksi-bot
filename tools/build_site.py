"""Build an allowlisted Pages artifact, never a copy of the entire repository."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'.html','.css','.js','.svg','.png','.jpg','.jpeg','.webp','.woff2','.woff','.ico','.txt','.xml'}
def build(output):
    output=Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise SystemExit('Refusing to overwrite a non-empty output directory')
    output.mkdir(parents=True,exist_ok=True)
    for source in (ROOT/'site').rglob('*'):
        if not source.is_file() or source.is_symlink():continue
        rel=source.relative_to(ROOT/'site')
        if any(p.startswith('.') for p in rel.parts):continue
        if source.suffix.lower() not in ALLOWED and source.name not in {'_headers','_redirects'}:continue
        target=output/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    (output/'release.json').write_text(json.dumps({'release':'2026-10-14.1','commit':commit,'auth_api':2},indent=2)+'\n')
    print('Static artifact prepared:',output)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output');args=parser.parse_args();build(args.output)
