#!/usr/bin/env python3
"""One version/source inventory; archive digest lives in a nonrecursive sidecar."""
import hashlib,json,pathlib,subprocess,zipfile
ROOT=pathlib.Path(__file__).resolve().parent

def digest(data):return hashlib.sha256(data).hexdigest()
def package():
    release=json.loads((ROOT/'release.json').read_text());version=release['version']
    if json.loads((ROOT/'package.json').read_text())['version']!=version:raise ValueError('version mismatch')
    source_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    names=['index.html','app-core.js','app-ui.js','app-cinema.js','service-worker.js','manifest.json','release.json','package.json','package-lock.json','package_project.py','README.md','INSTALL.md','requirements-vocal.txt']
    names+=['icons/icon.svg','icons/icon-192.png','icons/icon-512.png']
    names+=[str(p.relative_to(ROOT)) for p in (ROOT/'tools').iterdir() if p.suffix in {'.py','.cjs','.md'}]
    names=sorted(set(names));inventory={}
    for name in names:
        data=(ROOT/name).read_bytes();inventory[name]=digest(data)
        # Published release source must match the identified Git commit.
        committed=subprocess.check_output(['git','show',source_sha+':'+name],cwd=ROOT)
        if data!=committed:raise ValueError('uncommitted release source: '+name)
    manifest={'release_version':version,'repo_source_sha':source_sha,'runtime_contract':release['runtime_contract'],'packager_sha256':inventory['package_project.py'],'checksums':inventory,'certifier_identities':{k:v for k,v in inventory.items() if k.startswith('tools/certify_')}}
    out=ROOT/'dist';out.mkdir(exist_ok=True);filename=f'SoundForge-Studio-Release-v{version}.zip';archive=out/filename
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(ROOT/name).read_bytes())
        z.writestr('Release-Provenance-Manifest.json',json.dumps(manifest,sort_keys=True,indent=2))
    with zipfile.ZipFile(archive) as z:
        if z.testzip():raise ValueError('bad archive')
        for name,expected in inventory.items():
            if digest(z.read(name))!=expected:raise ValueError(name)
    receipt={'version':version,'repo_source_sha':source_sha,'package_filename':filename,'package_sha256':digest(archive.read_bytes()),'package_bytes':archive.stat().st_size,'source_inventory_entries':len(inventory),'manifest_sha256':digest(json.dumps(manifest,sort_keys=True,indent=2).encode()),'manifest':manifest}
    (out/(filename+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='manifest'},indent=2))
if __name__=='__main__':package()
