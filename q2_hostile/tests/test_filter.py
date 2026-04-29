import gzip
import json
from pathlib import Path
import tempfile
from unittest.mock import MagicMock
from unittest.mock import patch

from qiime2.plugin.testing import TestPluginBase
from q2_types.per_sample_sequences import CasavaOneEightSingleLanePerSampleDirFmt

from q2_hostile._formats import HostileIndexDirFmt
from q2_hostile.filter import filter_reads


class TestFilterReads(TestPluginBase):
    package = 'q2_hostile.tests'

    def setUp(self):
        self.reads = tempfile.TemporaryDirectory()
        self.index = tempfile.TemporaryDirectory()
        self.output = tempfile.TemporaryDirectory()

        self.reads_dir = Path(self.reads.name)
        self.index_dir = Path(self.index.name)
        self.output_dir = Path(self.output.name)

    def tearDown(self):
        self.reads.cleanup()
        self.index.cleanup()
        self.output.cleanup()

    def _mock_tempdir(self):
        mock_tempdir = MagicMock()
        mock_tempdir.__enter__.return_value = self.output_dir
        mock_tempdir.__exit__.return_value = None
        return mock_tempdir

    def _write_fastq(self, directory, filename):
        with gzip.open(Path(directory, filename), 'wt') as fh:
            fh.write('@read-1\nA\n+\n!\n')

    def _make_reads(self, paired=False):
        self._write_fastq(self.reads_dir, 'S1_0_L001_R1_001.fastq.gz')
        if paired:
            self._write_fastq(self.reads_dir, 'S1_0_L001_R2_001.fastq.gz')
        return CasavaOneEightSingleLanePerSampleDirFmt(
            str(self.reads_dir),
            mode='r',
        )

    def _make_index(self, aligner='both'):
        Path(self.index_dir, 'index.json').write_text(json.dumps({
            'name': 'human-t2t-hla',
            'aligner': aligner,
        }))

        if aligner in ('both', 'minimap2'):
            Path(self.index_dir, 'human-t2t-hla.fa.gz').write_bytes(b'index')
        if aligner in ('both', 'bowtie2'):
            Path(self.index_dir, 'human-t2t-hla.1.bt2').write_bytes(b'index')

        return HostileIndexDirFmt(str(self.index_dir), mode='r')

    def _fake_hostile_clean(self, cmd, env=None):
        output_dir = Path(cmd[cmd.index('--output') + 1])
        fastq1 = Path(cmd[cmd.index('--fastq1') + 1])

        self._write_fastq(
            output_dir,
            f'{self._fastq_stem(fastq1)}.clean.fastq.gz',
        )

        if '--fastq2' in cmd:
            fastq2 = Path(cmd[cmd.index('--fastq2') + 1])
            self._write_fastq(
                output_dir,
                f'{self._fastq_stem(fastq1)}.clean_1.fastq.gz',
            )
            self._write_fastq(
                output_dir,
                f'{self._fastq_stem(fastq2)}.clean_2.fastq.gz',
            )

        return ''

    def _fastq_stem(self, fastq):
        return fastq.name.removesuffix('.gz').removesuffix('.fastq')

    def _observed_result_files(self, result):
        return sorted(path.name for path in Path(result.path).iterdir())

    @patch('q2_hostile.filter.tempfile.TemporaryDirectory')
    @patch('q2_hostile.filter._run_hostile')
    def test_filter_reads_single_end_uses_artifact_index_and_preserves_name(
        self,
        mock_run_hostile,
        mock_temporary_directory,
    ):
        mock_temporary_directory.return_value = self._mock_tempdir()
        mock_run_hostile.side_effect = self._fake_hostile_clean
        reads = self._make_reads()
        index = self._make_index()

        observed = filter_reads(reads, index)

        sample_output = Path(self.output_dir, 'S1')
        mock_run_hostile.assert_called_once_with([
            'hostile',
            'clean',
            '--fastq1',
            str(Path(self.reads_dir, 'S1_0_L001_R1_001.fastq.gz')),
            '--index',
            str(Path(self.index_dir, 'human-t2t-hla.fa.gz')),
            '--aligner',
            'auto',
            '--threads',
            '1',
            '--output',
            str(sample_output),
            '--force',
            '--airplane',
        ])
        self.assertEqual(
            self._observed_result_files(observed),
            ['S1_0_L001_R1_001.fastq.gz'],
        )

    @patch('q2_hostile.filter.tempfile.TemporaryDirectory')
    @patch('q2_hostile.filter._run_hostile')
    def test_filter_reads_paired_end_uses_bowtie2_index_and_preserves_names(
        self,
        mock_run_hostile,
        mock_temporary_directory,
    ):
        mock_temporary_directory.return_value = self._mock_tempdir()
        mock_run_hostile.side_effect = self._fake_hostile_clean
        reads = self._make_reads(paired=True)
        index = self._make_index()

        observed = filter_reads(
            reads,
            index,
            threads=3,
            invert=True,
            rename=True,
            reorder=True,
        )

        sample_output = Path(self.output_dir, 'S1')
        mock_run_hostile.assert_called_once_with([
            'hostile',
            'clean',
            '--fastq1',
            str(Path(self.reads_dir, 'S1_0_L001_R1_001.fastq.gz')),
            '--index',
            str(Path(self.index_dir, 'human-t2t-hla')),
            '--aligner',
            'auto',
            '--threads',
            '3',
            '--output',
            str(sample_output),
            '--force',
            '--airplane',
            '--fastq2',
            str(Path(self.reads_dir, 'S1_0_L001_R2_001.fastq.gz')),
            '--invert',
            '--rename',
            '--reorder',
        ])
        self.assertEqual(
            self._observed_result_files(observed),
            [
                'S1_0_L001_R1_001.fastq.gz',
                'S1_0_L001_R2_001.fastq.gz',
            ],
        )

    @patch('q2_hostile.filter._run_hostile')
    def test_filter_reads_raises_when_index_lacks_required_aligner(
        self,
        mock_run_hostile,
    ):
        reads = self._make_reads(paired=True)
        index = self._make_index(aligner='minimap2')

        with self.assertRaisesRegex(
            ValueError,
            'filtering run requires bowtie2',
        ):
            filter_reads(reads, index)

        mock_run_hostile.assert_not_called()
