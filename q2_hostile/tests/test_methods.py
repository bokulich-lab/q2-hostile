import json
from pathlib import Path
from unittest.mock import patch

from qiime2.plugin.testing import TestPluginBase

from q2_hostile._formats import HostileIndexDirFmt
from q2_hostile._methods import fetch_index


class FetchIndexTests(TestPluginBase):
    package = 'q2_hostile.tests'

    def _fake_fetch(self, cmd, env=None):
        cache_dir = Path(env['HOSTILE_CACHE_DIR'])
        name = cmd[cmd.index('--name') + 1]

        if '--bowtie2' not in cmd:
            for suffix in ('.fa.gz', '.mmi'):
                Path(cache_dir, f'{name}{suffix}').write_bytes(b'index')

        if '--minimap2' not in cmd:
            for suffix in (
                '.1.bt2',
                '.2.bt2',
                '.3.bt2',
                '.4.bt2',
                '.rev.1.bt2',
                '.rev.2.bt2',
            ):
                Path(cache_dir, f'{name}{suffix}').write_bytes(b'index')

        return ''

    @patch('q2_hostile._methods._run_hostile')
    def test_fetch_index_copies_all_index_files(self, mock_run_hostile):
        mock_run_hostile.side_effect = self._fake_fetch

        observed = fetch_index(name='human-t2t-hla', aligner='both')

        self.assertIsInstance(observed, HostileIndexDirFmt)
        self.assertTrue(Path(observed.path, 'human-t2t-hla.fa.gz').is_file())
        self.assertTrue(Path(observed.path, 'human-t2t-hla.mmi').is_file())
        self.assertTrue(Path(observed.path, 'human-t2t-hla.1.bt2').is_file())
        self.assertTrue(Path(observed.path, 'human-t2t-hla.rev.2.bt2').is_file())

        metadata = json.loads(Path(observed.path, 'index.json').read_text())
        self.assertEqual(metadata, {'name': 'human-t2t-hla', 'aligner': 'both'})

        mock_run_hostile.assert_called_once()
        cmd = mock_run_hostile.call_args.args[0]
        env = mock_run_hostile.call_args.kwargs['env']
        self.assertEqual(cmd, ['hostile', 'index', 'fetch',
                               '--name', 'human-t2t-hla'])
        self.assertIn('HOSTILE_CACHE_DIR', env)

    @patch('q2_hostile._methods._run_hostile')
    def test_fetch_index_copies_minimap2_only(self, mock_run_hostile):
        mock_run_hostile.side_effect = self._fake_fetch

        observed = fetch_index(name='human-t2t-hla', aligner='minimap2')

        self.assertTrue(Path(observed.path, 'human-t2t-hla.fa.gz').is_file())
        self.assertTrue(Path(observed.path, 'human-t2t-hla.mmi').is_file())
        self.assertFalse(Path(observed.path, 'human-t2t-hla.1.bt2').exists())

        metadata = json.loads(Path(observed.path, 'index.json').read_text())
        self.assertEqual(metadata,
                         {'name': 'human-t2t-hla', 'aligner': 'minimap2'})

        mock_run_hostile.assert_called_once()
        cmd = mock_run_hostile.call_args.args[0]
        self.assertEqual(cmd, ['hostile', 'index', 'fetch',
                               '--name', 'human-t2t-hla', '--minimap2'])

    @patch('q2_hostile._methods._run_hostile')
    def test_fetch_index_copies_bowtie2_only(self, mock_run_hostile):
        mock_run_hostile.side_effect = self._fake_fetch

        observed = fetch_index(name='human-t2t-hla', aligner='bowtie2')

        self.assertFalse(Path(observed.path, 'human-t2t-hla.fa.gz').exists())
        self.assertTrue(Path(observed.path, 'human-t2t-hla.1.bt2').is_file())
        self.assertTrue(Path(observed.path, 'human-t2t-hla.rev.2.bt2').is_file())

        metadata = json.loads(Path(observed.path, 'index.json').read_text())
        self.assertEqual(metadata,
                         {'name': 'human-t2t-hla', 'aligner': 'bowtie2'})

        mock_run_hostile.assert_called_once()
        cmd = mock_run_hostile.call_args.args[0]
        self.assertEqual(cmd, ['hostile', 'index', 'fetch',
                               '--name', 'human-t2t-hla', '--bowtie2'])

    @patch('q2_hostile._methods._run_hostile')
    def test_fetch_index_raises_if_no_files_are_fetched(self, mock_run_hostile):
        mock_run_hostile.return_value = ''

        with self.assertRaisesRegex(
            FileNotFoundError,
            "Hostile did not fetch any index files for 'missing-index'",
        ):
            fetch_index(name='missing-index', aligner='both')
