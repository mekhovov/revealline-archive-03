import tempfile,unittest,subprocess,hashlib,tarfile,io,json,copy
from pathlib import Path
from prepare import REPO,validate_lock,scan,verify_directories,copy_frozen_site,verify_frozen_source,verify_tar_members
class ArtifactDirectoryTests(unittest.TestCase):
 def test_exact_tree(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/'a').mkdir();(r/'a/x').write_bytes(b'x');verify_directories(r,scan(r))
 def test_empty_hidden_directory_is_not_an_accepted_file_inventory(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/'x').write_bytes(b'x');expected=scan(r);(r/'.git').mkdir()
   self.assertEqual(scan(r),expected)
   with self.assertRaisesRegex(RuntimeError,'directory'):verify_directories(r,expected)
 def test_empty_ordinary_directory_is_not_an_accepted_file_inventory(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/'x').write_bytes(b'x');expected=scan(r);(r/'unlisted').mkdir()
   with self.assertRaisesRegex(RuntimeError,'directory'):verify_directories(r,expected)
 def test_directory_link_is_refused(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);(r/'a').mkdir();(r/'a/x').write_bytes(b'x');expected=scan(r);(r/'link').symlink_to(r/'a',target_is_directory=True)
   with self.assertRaisesRegex(RuntimeError,'symlink'):scan(r)
   with self.assertRaisesRegex(RuntimeError,'directory'):verify_directories(r,expected)
class FrozenCopyTests(unittest.TestCase):
 def test_copy_preserves_hidden_bytes_and_original(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);original=root/'frozen';original.mkdir();(original/'.xonix-build.json').write_bytes(b'original');(original/'game').mkdir();(original/'game/index.html').write_bytes(b'game');before=scan(original)
   copy_frozen_site(original,root/'copy');self.assertEqual(scan(root/'copy'),before);self.assertEqual(scan(original),before)
 def test_symlink_refused_before_copy(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);original=root/'frozen';original.mkdir();(root/'outside').write_bytes(b'x');(original/'link').symlink_to(root/'outside')
   with self.assertRaisesRegex(RuntimeError,'regular'):copy_frozen_site(original,root/'copy')
   self.assertFalse((root/'copy').exists())
 def test_extra_empty_directory_refused_before_copy(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);original=root/'frozen';original.mkdir();(original/'x').write_bytes(b'x');(original/'.extra').mkdir()
   with self.assertRaisesRegex(RuntimeError,'directory'):copy_frozen_site(original,root/'copy')
   self.assertFalse((root/'copy').exists())
 def test_existing_destination_is_retained(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);original=root/'frozen';original.mkdir();(original/'x').write_bytes(b'x');target=root/'copy';target.mkdir();(target/'prior').write_bytes(b'prior')
   with self.assertRaises(FileExistsError):copy_frozen_site(original,target)
   self.assertEqual(scan(target),[{'path':'prior','bytes':5,'sha256':__import__('hashlib').sha256(b'prior').hexdigest()}])
class FrozenSourceStreamTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.repo=self.root/'repo';self.repo.mkdir()
  def git(*args):return subprocess.check_output(['git',*args],cwd=self.repo,stderr=subprocess.DEVNULL)
  self.git=git;git('init','--quiet');git('config','user.name','Archive fixture');git('config','user.email','fixture@example.invalid')
  (self.repo/'source.txt').write_bytes(b'original source\n')
  git('add','source.txt');git('-c','commit.gpgsign=false','commit','--quiet','-m','Fixture')
  self.commit=git('rev-parse','HEAD').decode().strip();self.raw=git('archive','--format=tar',self.commit)
  self.tar=self.root/'source.tar';self.tar.write_bytes(self.raw);self.sha=hashlib.sha256(self.raw).hexdigest()
  self.entries={'source.txt':('100644',git('rev-parse','HEAD:source.txt').decode().strip())}
 def test_real_git_stream_and_members_without_extraction(self):
  self.assertEqual(verify_frozen_source(self.repo,self.tar,self.commit,self.sha),{'files':1,'bytes':16})
  self.assertEqual(self.tar.read_bytes(),self.raw);self.assertEqual(sorted(p.name for p in self.root.iterdir()),['repo','source.tar'])
 def test_changed_tar_refused_even_with_caller_rehashed_digest(self):
  changed=self.raw.replace(b'original source\n',b'altered! source\n');self.assertNotEqual(changed,self.raw);self.tar.write_bytes(changed)
  with self.assertRaisesRegex(RuntimeError,'differs'):verify_frozen_source(self.repo,self.tar,self.commit,hashlib.sha256(changed).hexdigest())
 def test_extra_raw_tail_refused(self):
  self.tar.write_bytes(self.raw+b'extra')
  with self.assertRaisesRegex(RuntimeError,'extra bytes'):verify_frozen_source(self.repo,self.tar,self.commit,self.sha)
 def test_record_digest_is_still_authoritative(self):
  with self.assertRaisesRegex(RuntimeError,'Fresh source TAR differs'):verify_frozen_source(self.repo,self.tar,self.commit,'0'*64)
 def test_source_tar_symlink_refused(self):
  link=self.root/'link.tar';link.symlink_to(self.tar)
  with self.assertRaisesRegex(RuntimeError,'Non-regular'):verify_frozen_source(self.repo,link,self.commit,self.sha)
 def custom_tar(self,member,body=b'x'):
  with tarfile.open(self.tar,'w',format=tarfile.PAX_FORMAT,pax_headers={'comment':self.commit}) as archive:
   archive.addfile(member,io.BytesIO(body) if member.isfile() else None)
 def test_member_blob_authority_independent_of_raw_digest(self):
  member=tarfile.TarInfo('source.txt');member.size=1;self.custom_tar(member)
  with self.assertRaisesRegex(RuntimeError,'blob differs'):verify_tar_members(self.tar,self.commit,self.entries)
 def test_special_and_unsafe_members_refused(self):
  for name,kind,error in [('source.txt',tarfile.SYMTYPE,'special/link'),('../source.txt',tarfile.REGTYPE,'Unsafe path')]:
   with self.subTest(name=name):
    member=tarfile.TarInfo(name);member.type=kind;member.linkname='outside';self.custom_tar(member)
    with self.assertRaisesRegex(RuntimeError,error):verify_tar_members(self.tar,self.commit,self.entries)
 def test_missing_git_member_and_changed_mode_refused(self):
  with self.assertRaisesRegex(RuntimeError,'Missing TAR'):verify_tar_members(self.tar,self.commit,{**self.entries,'missing':('100644','0'*40)})
  with self.assertRaisesRegex(RuntimeError,'mode differs'):verify_tar_members(self.tar,self.commit,{'source.txt':('100755',self.entries['source.txt'][1])})
class LockAuthorityTests(unittest.TestCase):
 def setUp(self):
  self.lock=json.loads((REPO/'source-lock.json').read_text());self.plan=json.loads((REPO/'pages-archives.json').read_text());self.package={'version':'0.36.0'}
 def check(self):validate_lock(self.lock,self.plan,self.package)
 def test_exact_prepared_authority(self):self.check()
 def test_wrong_shard_repository_or_selected_editions_refused(self):
  for field,value in [('archiveId','archive-02'),('archiveRepository','foreign/archive-03'),('selectedVersions',['v0.34.0'])]:
   with self.subTest(field=field):
    original=copy.deepcopy(self.lock);self.lock[field]=value
    with self.assertRaises(RuntimeError):self.check()
    self.lock=original
 def test_plan_cannot_silently_name_another_repository(self):
  self.plan['shards'][-1]['repository']='foreign/archive-03'
  with self.assertRaisesRegex(RuntimeError,'Allocation target'):self.check()
 def test_controller_version_and_source_refused(self):
  self.package['version']='0.35.0'
  with self.assertRaisesRegex(RuntimeError,'controller version'):self.check()
  self.package['version']='0.36.0';self.lock['sourceCommit']='0'*40
  with self.assertRaisesRegex(RuntimeError,'controller source'):self.check()
 def test_all_history_includes_nonsemantic_tag_and_exact_objects(self):
  original=copy.deepcopy(self.lock)
  self.lock['tagObjects']=[r for r in self.lock['tagObjects'] if r[0]!='v0.0.9-motion-lab']
  with self.assertRaisesRegex(RuntimeError,'history count'):self.check()
  self.lock=original;self.lock['releases'][0]['tagObject']='0'*40
  with self.assertRaisesRegex(RuntimeError,'tag authority'):self.check()
 def test_higher_budget_is_refused(self):
  self.lock['archiveBudgetBytes']+=1
  with self.assertRaisesRegex(RuntimeError,'capacity/runtime'):self.check()
if __name__=='__main__':unittest.main()
