import json
from pathlib import Path
import subprocess

from q2_hostile._formats import HostileIndexDirFmt


def _run_command(cmd):
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        raise RuntimeError(
            f'{cmd[0]} failed with exit code {exc.returncode}: {detail}'
        ) from exc


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
