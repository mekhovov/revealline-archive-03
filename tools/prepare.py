#!/usr/bin/env python3
"""Verify three immutable sites and assemble a strictly pinned archive; never freeze or tag."""
import argparse,hashlib,json,os,re,shutil,stat,subprocess,tarfile,zipfile
from pathlib import Path,PurePosixPath
REPO=Path(__file__).resolve().parents[1]
H=lambda b:hashlib.sha256(b).hexdigest()
def require(ok,msg):
 if not ok:raise RuntimeError(msg)
def safe(s):
 p=PurePosixPath(s)
 require(s and not p.is_absolute() and '\\' not in s and not any(c in ('','.', '..') for c in s.split('/')) and not any(ord(c)<32 for c in s),'Unsafe path '+repr(s))
 return p
def scan(root):
 result=[]
 for d,dirs,files in os.walk(root,followlinks=False):
  for n in dirs:require(not (Path(d)/n).is_symlink(),'Directory symlink')
  for n in files:
   p=Path(d)/n;require(stat.S_ISREG(p.lstat().st_mode),'Non-regular file')
   b=p.read_bytes();result.append({'path':p.relative_to(root).as_posix(),'bytes':len(b),'sha256':H(b)})
 return sorted(result,key=lambda x:x['path'])
def verify_directories(root,files):
 expected={"."}
 for row in files:
  p=PurePosixPath(row['path']).parent
  while str(p)!=".":expected.add(str(p));p=p.parent
 actual={"."}
 for directory,children,_ in os.walk(root,followlinks=False):
  for name in children:
   p=Path(directory)/name;require(p.is_dir() and not p.is_symlink(),"Non-ordinary artifact directory")
   actual.add(p.relative_to(root).as_posix())
 require(actual==expected,"Unexpected or missing artifact directory")
def copy_frozen_site(original,site):
 rows=scan(original);verify_directories(original,rows)
 require(bool(rows),'Empty frozen site')
 shutil.copytree(original,site)
def write(p,value):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False);f.write('\n')
def verify_tar_members(tarPath,commit,entries):
 """Verify bounded original TAR bodies against Git blobs without extracting another tree."""
 seen=set();files=set();total=0
 with tarfile.open(tarPath,'r:') as ar:
  require(ar.pax_headers.get('comment')==commit,'TAR commit differs')
  for m in ar:
   key=str(safe(m.name.rstrip('/') if m.isdir() else m.name))
   require(key not in seen,'Duplicate TAR path');seen.add(key)
   require(len(seen)<20000,'TAR aggregate bound')
   require(m.isfile() or m.isdir(),'TAR special/link')
   if m.isdir():continue
   require(0<=m.size<=64*1024*1024,'TAR member bound');total+=m.size
   require(total<=1024**3,'TAR aggregate bound')
   require(key in entries,'Unexpected TAR source member')
   mode,oid=entries[key];require(bool(m.mode&0o111)==(mode=='100755'),'TAR executable mode differs')
   b=ar.extractfile(m).read();require(len(b)==m.size,'Truncated TAR')
   require(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid,'TAR source blob differs')
   files.add(key)
 require(files==set(entries),'Missing TAR source member')
 return {'files':len(files),'bytes':total}
def verify_frozen_source(root,tarPath,commit,expectedSha256):
 """The explicit local reuse mode still requires exact freshly streamed git-archive bytes."""
 require(stat.S_ISREG(tarPath.lstat().st_mode),'Non-regular frozen source TAR')
 process=subprocess.Popen(['git','archive','--format=tar',commit],cwd=root,stdout=subprocess.PIPE)
 digest=hashlib.sha256()
 try:
  with tarPath.open('rb') as original:
   while True:
    b=process.stdout.read(1024*1024)
    require(original.read(len(b))==b,'Frozen source TAR differs from fresh Git stream')
    if not b:
     require(original.read(1)==b'','Frozen source TAR has extra bytes');break
    digest.update(b)
  require(process.wait()==0,'Git archive failed')
 finally:
  process.stdout.close()
  if process.poll() is None:process.kill()
  process.wait()
 require(digest.hexdigest()==expectedSha256,'Fresh source TAR differs')
 entries={}
 for entry in filter(None,subprocess.check_output(['git','ls-tree','-rz',commit],cwd=root).split(b'\0')):
  meta,name=entry.split(b'\t',1);mode,kind,oid=meta.split();name=name.decode();safe(name)
  require(kind==b'blob' and mode in (b'100644',b'100755'),'Unsupported Git member')
  require(name not in entries,'Duplicate Git source member');entries[name]=(mode.decode(),oid.decode())
 return verify_tar_members(tarPath,commit,entries)
def validate_lock(lock,plan,package):
 require(lock['sourceRepository']=='mekhovov/revealline' and lock['archiveId']=='archive-03' and lock['archiveRepository']=='mekhovov/revealline-archive-03','Archive target identity differs')
 require(lock['currentVersion']=='v0.37.0' and 'v'+package['version']==lock['currentVersion'],'Current controller version differs')
 require(lock['selectedVersions']==['v0.33.0','v0.34.0','v0.35.0'],'Selected editions differ')
 selected=[s for s in plan['shards'] if s['id']==lock['archiveId']]
 require(selected==[{'id':lock['archiveId'],'repository':lock['archiveRepository'],'versions':lock['selectedVersions']}],'Allocation target differs')
 require(lock['archiveBudgetBytes']==800_000_000 and lock['node']=='v22.22.2','Archive capacity/runtime differs')
 records=lock['releases'];tags=lock['tagObjects']
 require(len(records)==44 and len({r['version'] for r in records})==44 and len(tags)==45 and len(dict(tags))==45 and tags==sorted(tags),'Complete history count differs')
 require({n:o for n,o in tags if re.fullmatch(r'v\d+\.\d+\.\d+',n)}=={r['version']:r['tagObject'] for r in records},'History tag authority differs')
 current=[r for r in records if r['version']==lock['currentVersion']]
 require(len(current)==1 and current[0]['commit']==lock['sourceCommit'],'Current controller source differs')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--git-root',required=True);ap.add_argument('--builder-source',required=True);ap.add_argument('--out',required=True);ap.add_argument('--frozen-root');ap.add_argument('--reuse-frozen-sites',action='store_true');a=ap.parse_args();require(not a.reuse_frozen_sites or a.frozen_root,'Frozen reuse requires --frozen-root')
 root=Path(a.git_root).resolve();source=Path(a.builder_source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
 lock=json.loads((REPO/'source-lock.json').read_text());expectedRaw=(REPO/'expected-inventory.json').read_bytes();expected=json.loads(expectedRaw)
 require(H(expectedRaw)==lock['expectedInventorySha256'],'Expected inventory changed')
 require(H((REPO/'pages-archives.json').read_bytes())==lock['allocationSha256'],'Allocation changed')
 validate_lock(lock,json.loads((REPO/'pages-archives.json').read_text()),json.loads((source/'package.json').read_text()))
 def git(*args):return subprocess.check_output(['git',*args],cwd=root)
 def tags():return sorted((n,git('rev-parse','refs/tags/'+n).decode().strip()) for n in git('tag','--list').decode().splitlines())
 priorTags=tags();write(out/'tags-before.json',priorTags)
 def source_guards():
  require([list(r) for r in tags()]==lock['tagObjects'],'Complete Git tag set changed; re-review before publication')
  current={n:o for n,o in tags() if re.fullmatch(r'v\d+\.\d+\.\d+',n)}
  require(current=={r['version']:r['tagObject'] for r in lock['releases']},'Frozen release tag set changed; re-review before publication')
  for r in lock['releases']:require(git('rev-parse','refs/tags/'+r['version']+'^{commit}').decode().strip()==r['commit'],'Tag commit changed')
  for p in lock['contracts']:require(H((source/p['path']).read_bytes())==p['sha256'],'Builder source contract changed: '+p['path'])
 def git_files_equal(directory,commit):
  tree=git('ls-tree','-rz',commit).split(b'\0');total=0;count=0
  for entry in filter(None,tree):
   meta,name=entry.split(b'\t',1);mode,kind,oid=meta.split();name=name.decode();safe(name)
   require(kind==b'blob' and mode in (b'100644',b'100755'),'Unsupported Git member')
   p=directory/name;require(p.is_file() and not p.is_symlink(),'Missing ordinary source: '+name);b=p.read_bytes()
   require(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid.decode(),'Source blob changed: '+name);total+=len(b);count+=1
  return {'files':count,'bytes':total}
 source_guards();builderTree=git_files_equal(source,lock['sourceCommit'])
 require(subprocess.check_output(['node','-p','process.version'],text=True).strip()==lock['node'],'Wrong Node runtime')
 frozen=Path(a.frozen_root).resolve() if a.frozen_root else None
 selected=lock['selectedVersions'];before={}
 if frozen:
  for v in selected:before[v]=scan(frozen/v)
  write(out/'frozen-before.json',before)
 project=out/'project';project.mkdir();(project/'releases').mkdir()
 gitdir=git('rev-parse','--absolute-git-dir').decode().strip();(project/'.git').write_text('gitdir: '+gitdir+'\n')
 shutil.copyfile(source/'package.json',project/'package.json')
 audits=[]
 for r in lock['releases']:
  recordRaw=r['recordUtf8'].encode();require(len(recordRaw)==r['recordBytes'] and H(recordRaw)==r['recordSha256'],'Record pin inconsistent')
  record=json.loads(recordRaw);target=project/'releases'/r['version'];target.mkdir()
  (target/'release.json').write_bytes(recordRaw)
  if r['version'] not in selected:continue
  v=r['version'];work=out/v;work.mkdir();tarPath=work/'source.tar'
  if a.reuse_frozen_sites:
   sourceTree=verify_frozen_source(root,frozen/v/'source.tar',r['commit'],record['sourceArchiveSha256'])
  else:
   with tarPath.open('xb') as stream:subprocess.run(['git','archive','--format=tar',r['commit']],cwd=root,stdout=stream,check=True)
   raw=tarPath.read_bytes();require(H(raw)==record['sourceArchiveSha256'],'Fresh source TAR differs')
   if frozen:require(raw==(frozen/v/'source.tar').read_bytes(),'Frozen source TAR differs')
   extracted=work/'source';extracted.mkdir();seen=set();total=0
   with tarfile.open(tarPath,'r:') as ar:
    require(ar.pax_headers.get('comment')==r['commit'],'TAR commit differs')
    for m in ar:
     p=safe(m.name.rstrip('/') if m.isdir() else m.name);key=str(p);require(key not in seen,'Duplicate TAR path');seen.add(key)
     require(m.isfile() or m.isdir(),'TAR special/link')
     if m.isdir():continue
     require(0<=m.size<=64*1024*1024,'TAR member bound');total+=m.size;require(total<=1024**3 and len(seen)<20000,'TAR aggregate bound')
     b=ar.extractfile(m).read();require(len(b)==m.size,'Truncated TAR');dest=extracted/p;dest.parent.mkdir(parents=True,exist_ok=True)
     with dest.open('xb') as stream:stream.write(b)
     dest.chmod(m.mode&0o777)
   sourceTree=git_files_equal(extracted,r['commit'])
  site=target/'site'
  if a.reuse_frozen_sites:
   # Caller-owned frozen sites are copied only after their source TAR equals the exact tag.
   # The same manifest, ZIP, loose-byte, accepted-inventory and post-run checks below remain mandatory.
   copy_frozen_site(frozen/v/'site',site)
  else:
   with (work/'build.stdout').open('xb') as stdout,(work/'build.stderr').open('xb') as stderr:
    cmd=['node',str(extracted/'scripts/game-cli.mjs'),'build','--out',str(site),'--version',v,'--revision',r['commit']]
    write(work/'build-command.json',cmd);subprocess.run(cmd,cwd=extracted,stdout=stdout,stderr=stderr,check=True)
  manifestRaw=(site/'manifest.json').read_bytes();zipRaw=(site/'distribution.zip').read_bytes()
  require(H(manifestRaw)==record['manifestSha256'] and H(zipRaw)==record['distributionSha256'],'Fresh manifest/ZIP differs from frozen release')
  manifest=json.loads(manifestRaw);require(manifest['version']==v and manifest['sourceRevision']==r['commit'],'Manifest identity differs')
  rows=scan(site);lookup={x['path']:x for x in rows};names=set();assetBytes=0
  for x in manifest['files']:
   safe(x['path']);require(x['path'] not in names and lookup.get(x['path'])==x,'Manifest payload differs');names.add(x['path']);assetBytes+=x['bytes']
  require(assetBytes==manifest['totalBytes'],'Manifest total differs')
  require(set(lookup)==names|{'manifest.json','distribution.zip','distribution.zip.sha256','.xonix-build.json'},'Unexpected loose inventory')
  require((site/'distribution.zip.sha256').read_text()==record['distributionSha256']+'  distribution.zip\n','Checksum differs')
  require(json.loads((site/'.xonix-build.json').read_text())=={'tool':'xonix-game-cli','formatVersion':1},'Ownership metadata differs')
  with zipfile.ZipFile(site/'distribution.zip') as z:
   entries=z.infolist();require(len(entries)==len(names)+1 and {e.filename for e in entries}==names|{'manifest.json'},'ZIP inventory differs')
   for e in entries:
    safe(e.filename);require(not e.is_dir() and not (e.flag_bits&1) and stat.S_IFMT(e.external_attr>>16) in (0,stat.S_IFREG),'ZIP special/encrypted member')
    require(e.file_size<=256*1024*1024,'ZIP size bound')
   require(sum(e.file_size for e in entries)<=1024**3 and z.testzip() is None,'ZIP aggregate/CRC failure')
   for e in entries:require(z.read(e)==(site/e.filename).read_bytes(),'ZIP payload differs')
  if frozen:
   require(recordRaw==(frozen/v/'release.json').read_bytes(),'Original release record differs')
   require(rows==scan(frozen/v/'site'),'Frozen loose inventory differs')
   for x in rows:require((site/x['path']).read_bytes()==(frozen/v/'site'/x['path']).read_bytes(),'Frozen loose bytes differ')
  # Independent accepted inventory covers every published canonical payload, including hidden ownership and checksum.
  actual=[{'path':f'releases/{v}/site/'+x['path'],'bytes':x['bytes'],'sha256':x['sha256']} for x in rows if x['path']!='distribution.zip']
  wanted=[x for x in expected['files'] if x['path'].startswith(f'releases/{v}/site/')]
  require(actual==wanted,'Rebuilt site differs from pinned accepted public inventory')
  write(work/'site-inventory.json',rows);audits.append({'version':v,'commit':r['commit'],'sourceTree':sourceTree,'siteFiles':len(rows),'siteBytes':sum(x['bytes'] for x in rows),'manifestAssets':len(names),'zipMembers':len(entries),'record':record,'frozenByteEquality':bool(frozen),'siteMode':'verified-frozen-copy' if a.reuse_frozen_sites else 'archived-cli-rebuild'})
 staged=project/'.cache/archive03';buildScript=out/'build.mjs'
 buildScript.write_text('import {buildPages} from '+json.dumps((source/'scripts/build-pages.mjs').as_uri())+';\nimport fs from "node:fs/promises";\nconst result=await buildPages('+json.dumps({'projectRoot':str(project),'repository':lock['sourceRepository'],'archivePlan':json.loads((REPO/'pages-archives.json').read_text()),'archiveId':'archive-03','outputDirectory':str(staged)})+');\nawait fs.writeFile('+json.dumps(str(out/'build.json'))+',JSON.stringify(result,null,2)+"\\n",{flag:"wx"});\n')
 with (out/'build.stdout').open('xb') as stdout,(out/'build.stderr').open('xb') as stderr:subprocess.run(['node',str(buildScript)],cwd=project,stdout=stdout,stderr=stderr,check=True)
 artifact=out/'artifact';staged.rename(artifact);actual=scan(artifact)
 require(actual==expected['files'],'Archive path set or bytes differs from independent expected inventory')
 verify_directories(artifact,expected['files'])
 require(sum(x['bytes'] for x in actual)==expected['totalBytes']<=lock['archiveBudgetBytes'],'Archive budget differs')
 hidden=sorted(x['path'] for x in actual if any(c.startswith('.') for c in x['path'].split('/')))
 require(hidden==expected['hiddenFiles'],'Unexpected hidden content')
 source_guards();require(tags()==priorTags,'Git refs changed during preparation')
 if frozen:
  after={v:scan(frozen/v) for v in selected};require(after==before,'Frozen releases changed');write(out/'frozen-after.json',after)
 write(out/'tags-after.json',tags());write(out/'inventory.json',expected)
 write(out/'receipt.json',{'passed':True,'sourceCommit':lock['sourceCommit'],'builderTree':builderTree,'archiveId':'archive-03','fileCount':len(actual),'totalBytes':expected['totalBytes'],'hiddenFiles':hidden,'inventorySha256':H(expectedRaw),'selected':audits,'allReleaseTagsUnchanged':True,'selectedFrozenTreesUnchanged':bool(frozen),'siteMode':'verified-frozen-copy' if a.reuse_frozen_sites else 'archived-cli-rebuild','scope':'Local canonical verification/assembly only. No source edits, release creation, tag/ref mutation, repo publication, HTTP or browser execution.'})
 print(json.dumps({'passed':True,'files':len(actual),'bytes':expected['totalBytes'],'receipt':str(out/'receipt.json')}))
if __name__=='__main__':main()
