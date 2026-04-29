import gzip
import json
from pathlib import Path
import tempfile

from qiime2.plugin.testing import TestPluginBase
from q2_types.per_sample_sequences import CasavaOneEightSingleLanePerSampleDirFmt

from q2_hostile._formats import HostileIndexDirFmt
from q2_hostile._utils import run_command
from q2_hostile.filter import filter_reads


class TestFilterReadsIntegration(TestPluginBase):
    package = 'q2_hostile.tests'

    def setUp(self):
        self.workdir = tempfile.TemporaryDirectory()
        self.workdir_path = Path(self.workdir.name)
        self.reads_dir = self.workdir_path / 'reads'
        self.index_dir = self.workdir_path / 'index'
        self.reads_dir.mkdir()
        self.index_dir.mkdir()

    def tearDown(self):
        self.workdir.cleanup()

    def test_filter_reads_removes_host_read_with_bowtie2_index(self):
        reads = self._make_reads()
        index = self._make_bowtie2_index()

        observed = filter_reads(reads, index, aligner='bowtie2')

        output_path = Path(observed.path, 'S1_0_L001_R1_001.fastq.gz')
        self.assertTrue(output_path.is_file())
        self.assertEqual(self._read_fastq_ids(output_path), ['non-host'])

    def _make_reads(self):
        self._write_fastq(
            self.reads_dir / 'S1_0_L001_R1_001.fastq.gz',
            [
                (
                    'host',
                    'ACGTTGCAGTCAGTCAAGTCGATCGTACGATCGATGCTAGCTAGC',
                ),
                (
                    'non-host',
                    'CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC',
                ),
            ],
        )
        return CasavaOneEightSingleLanePerSampleDirFmt(
            str(self.reads_dir),
            mode='r',
        )

    def _make_bowtie2_index(self):
        reference_path = self.workdir_path / 'host.fa'
        reference_path.write_text(
            '>host\n'
            'ACGTTGCAGTCAGTCAAGTCGATCGTACGATCGATGCTAGCTAGC'
            'GATCCGATCGATCGTACGTAGCTAGCTAGCTACGATCGATCGATCGA\n'
        )
        index_prefix = self.index_dir / 'tiny-host'
        run_command(
            ['bowtie2-build', str(reference_path), str(index_prefix)],
            capture_output=True,
            text=True,
        )

        Path(self.index_dir, 'index.json').write_text(json.dumps({
            'name': 'tiny-host',
            'aligner': 'bowtie2',
        }))

        return HostileIndexDirFmt(str(self.index_dir), mode='r')

    def _write_fastq(self, path, records):
        with gzip.open(path, 'wt') as fh:
            for read_id, sequence in records:
                quality = 'I' * len(sequence)
                fh.write(f'@{read_id}\n{sequence}\n+\n{quality}\n')

    def _read_fastq_ids(self, path):
        read_ids = []
        with gzip.open(path, 'rt') as fh:
            for line_number, line in enumerate(fh):
                if line_number % 4 == 0:
                    read_ids.append(line.strip().removeprefix('@'))
        return read_ids
