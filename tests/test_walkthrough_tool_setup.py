"""Beginner readiness checks extracted from the actual lesson; no network in tests."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_revision_text_processing import CodeParser, PAGE

ROOT=Path(__file__).resolve().parents[1]
BASH=shutil.which('bash')


class SetupSourceTests(unittest.TestCase):
    def test_checkpoint_precedes_practice_inputs_and_has_working_lesson_anchors(self):
        text=PAGE.read_text()
        self.assertLess(text.index('id="cli-part2-tool-checkpoint"'),text.index('<pre id="cli-part2-setup"'))
        self.assertLess(text.index('<pre id="cli-part2-preflight"'),text.index('<pre id="cli-part2-setup"'))
        for name in ['cli-part2-micromamba-check','cli-part2-shell-hook','cli-part2-install','cli-part2-activate']:
            self.assertIn(name,CodeParser().named)
        self.assertIn('conda-mamba-part1.html#install-micromamba',text)
        self.assertIn('do not need R, Python, Scanpy or Seurat',text)
        mamba=(ROOT/'tutorials/conda-mamba-part1.html').read_text()
        self.assertIn('id="install-micromamba"',mamba)
        self.assertIn('id="qc-environment-lab"',mamba)
        self.assertIn('command-line-part2.html#cli-part2-tool-checkpoint',mamba)
        self.assertIn('Required route:',mamba)
        self.assertIn('Optional cleanup after you finish',mamba)
        self.assertIn('Optional reference: combine Python, R, and command-line tools',mamba)
        self.assertIn('not extra steps to run in sequence',mamba)
        self.assertIn('not needed for the Bash lessons, SeqKit setup or the authored YAML exercise',mamba)

    def test_seqkit_install_is_small_and_has_explicit_channel_policy(self):
        code=CodeParser().named['cli-part2-install']
        for item in ['-n cli-sequences','--override-channels','-c conda-forge -c bioconda','--channel-priority strict','seqkit']:
            self.assertIn(item,code)
        for item in ['r-base','scanpy','seurat','fastqc','multiqc','python=']:
            self.assertNotIn(item,code)


@unittest.skipUnless(BASH,'Bash required for local checkpoint contracts')
class SetupShellTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.bin=self.root/'bin';self.bin.mkdir()
        self.env=os.environ.copy()
        self.env.update({'HOME':str(self.root),'PATH':str(self.bin),'CALL_LOG':str(self.root/'calls'),'HOOK_MARKER':str(self.root/'marker')})
        self.env.pop('BASH_ENV',None);self.env.pop('ENV',None)
        self.code=CodeParser().named

    def tearDown(self):self.temp.cleanup()

    def run_bash(self,code):
        return subprocess.run([BASH,'--noprofile','--norc','-c',code],env=self.env,text=True,capture_output=True)

    def executable(self,name,body):
        path=self.bin/name;path.write_text('#!'+BASH+'\n'+body+'\n');path.chmod(0o755)

    def mock_micromamba(self):
        self.executable('micromamba','''printf '%s\\n' "$*" >> "$CALL_LOG"
if [[ "$1" == shell ]]; then
  if [[ "${FAIL_HOOK:-0}" == 1 ]]; then
    printf 'touch "$HOOK_MARKER"\\n'
    exit 42
  fi
  printf 'export CHECKPOINT_HOOK_READY=1\\n'
fi
if [[ "$1" == activate && "${FAIL_ACTIVATE:-0}" == 1 ]]; then exit 43; fi
''')

    def test_missing_micromamba_stops_its_check(self):
        result=self.run_bash(self.code['cli-part2-micromamba-check'])
        self.assertNotEqual(result.returncode,0)

    def test_current_shell_hook_is_loaded_when_successful(self):
        self.mock_micromamba()
        result=self.run_bash(self.code['cli-part2-shell-hook']+'\nprintf "%s\\n" "${CHECKPOINT_HOOK_READY:-missing}"')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'1')
        self.assertEqual((self.root/'calls').read_text().strip(),'shell hook --shell bash')

    def test_failed_hook_is_not_evaluated(self):
        self.mock_micromamba();self.env['FAIL_HOOK']='1'
        result=self.run_bash(self.code['cli-part2-shell-hook'])
        self.assertEqual(result.returncode,42)
        self.assertFalse((self.root/'marker').exists())

    def test_failed_activation_cannot_report_another_seqkit_as_success(self):
        self.mock_micromamba();self.env['FAIL_ACTIVATE']='1'
        self.executable('seqkit','printf "seqkit called\\n" >> "$CALL_LOG"; printf "mock version\\n"')
        result=self.run_bash(self.code['cli-part2-activate'])
        self.assertEqual(result.returncode,43)
        self.assertEqual((self.root/'calls').read_text().strip(),'activate cli-sequences')
        self.assertNotIn('mock version',result.stdout)

    def test_activation_then_version_check_has_a_positive_path(self):
        self.mock_micromamba()
        self.executable('seqkit','printf "seqkit called\\n" >> "$CALL_LOG"; printf "mock version\\n"')
        result=self.run_bash(self.code['cli-part2-activate'])
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('mock version',result.stdout)
        self.assertEqual((self.root/'calls').read_text().splitlines(),['activate cli-sequences','seqkit called'])

    def test_readiness_fails_before_version_if_a_required_utility_is_absent(self):
        self.executable('seqkit','printf "must not reach version\\n"')
        result=self.run_bash(self.code['cli-part2-preflight'])
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Missing tool: awk',result.stderr)
        self.assertNotIn('must not reach version',result.stdout)


if __name__=='__main__':unittest.main()
