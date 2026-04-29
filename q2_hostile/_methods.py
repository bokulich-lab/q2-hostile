import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from q2_types.per_sample_sequences import (
    CasavaOneEightSingleLanePerSampleDirFmt,
)

from q2_hostile._formats import HostileIndexDirFmt, HostileIndexMetadataFormat


def _run_command(cmd):
    try:
        completed = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        raise RuntimeError(
            f'{cmd[0]} failed with exit code {exc.returncode}: {detail}'
        ) from exc
    return completed.stdout


def fetch_index(
    name: str = 'human-t2t-hla',
    aligner: str = 'both',
) -> HostileIndexDirFmt:
    cmd = ['hostile', 'index', 'fetch', '--name', name]

    if aligner == 'minimap2':
        cmd.append('--minimap2')
    elif aligner == 'bowtie2':
        cmd.append('--bowtie2')

    _run_command(cmd)

    result = HostileIndexDirFmt()
    metadata = {
        'name': name,
        'aligner': aligner,
    }
    Path(result.path, 'index.json').write_text(
        json.dumps(metadata, indent=2) + '\n'
    )

    return result


def filter_reads(
    reads: CasavaOneEightSingleLanePerSampleDirFmt,
    index: HostileIndexDirFmt,
    aligner: str = 'auto',
    threads: int = 1,
    invert: bool = False,
    rename: bool = False,
    reorder: bool = False,
) -> CasavaOneEightSingleLanePerSampleDirFmt:
    index_metadata = _read_index_metadata(index)
    samples = reads.manifest
    paired = _is_paired(samples)
    _validate_index_aligner(index_metadata['aligner'], aligner, paired)

    result = CasavaOneEightSingleLanePerSampleDirFmt()

    with tempfile.TemporaryDirectory(prefix='q2-hostile-clean-') as tmpdir:
        tmpdir = Path(tmpdir)

        for sample_id, sample in samples.iterrows():
            sample_output = tmpdir / str(sample_id)
            sample_output.mkdir()
            cmd = _build_clean_command(
                fastq1=sample['forward'],
                fastq2=sample['reverse'] if paired else None,
                output_dir=sample_output,
                index=index_metadata['name'],
                aligner=aligner,
                threads=threads,
                invert=invert,
                rename=rename,
                reorder=reorder,
            )
            log = _parse_hostile_log(_run_command(cmd))
            record = log[0]

            _copy_cleaned_fastq(
                source=record['fastq1_out_path'],
                destination=Path(result.path, Path(sample['forward']).name),
            )
            if paired:
                _copy_cleaned_fastq(
                    source=record['fastq2_out_path'],
                    destination=Path(result.path, Path(sample['reverse']).name),
                )

    return result


def _read_index_metadata(index):
    with index.index.view(HostileIndexMetadataFormat).open() as fh:
        return json.load(fh)


def _is_paired(samples):
    return 'reverse' in samples and samples['reverse'].notna().any()


def _validate_index_aligner(index_aligner, requested_aligner, paired):
    if index_aligner == 'both':
        return

    if requested_aligner == 'auto':
        requested_aligner = 'bowtie2' if paired else 'minimap2'

    if index_aligner != requested_aligner:
        raise ValueError(
            f'The fetched index contains {index_aligner} files, but this '
            f'filtering run requires {requested_aligner}. Fetch the index '
            'again with aligner="both" or the required aligner.'
        )


def _build_clean_command(
    fastq1,
    fastq2,
    output_dir,
    index,
    aligner,
    threads,
    invert,
    rename,
    reorder,
):
    cmd = [
        'hostile',
        'clean',
        '--fastq1',
        str(fastq1),
        '--index',
        index,
        '--aligner',
        aligner,
        '--threads',
        str(threads),
        '--output',
        str(output_dir),
        '--force',
        '--airplane',
    ]

    if fastq2 is not None:
        cmd.extend(['--fastq2', str(fastq2)])
    if invert:
        cmd.append('--invert')
    if rename:
        cmd.append('--rename')
    if reorder:
        cmd.append('--reorder')

    return cmd


def _parse_hostile_log(stdout):
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        start = stdout.find('[')
        end = stdout.rfind(']')
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError(
                'Hostile completed but did not emit a JSON cleaning log.'
            ) from exc
        return json.loads(stdout[start:end + 1])


def _copy_cleaned_fastq(source, destination):
    shutil.copyfile(source, destination)
