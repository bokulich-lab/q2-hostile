import json
import os
from pathlib import Path
import shutil
import tempfile

from q2_hostile._formats import HostileIndexDirFmt
from q2_hostile._utils import run_command


def fetch_index(
    name: str = "human-t2t-hla",
    aligner: str = "both",
) -> HostileIndexDirFmt:
    cmd = ["hostile", "index", "fetch", "--name", name]

    if aligner == "minimap2":
        cmd.append("--minimap2")
    elif aligner == "bowtie2":
        cmd.append("--bowtie2")

    result = HostileIndexDirFmt()
    with tempfile.TemporaryDirectory(prefix="q2-hostile-index-") as cache_dir:
        env = os.environ.copy()
        env["HOSTILE_CACHE_DIR"] = cache_dir
        _run_hostile(cmd, env=env)
        _copy_fetched_index(name, aligner, cache_dir, result.path)

    metadata = {
        "name": name,
        "aligner": aligner,
    }
    Path(result.path, "index.json").write_text(json.dumps(metadata, indent=2) + "\n")

    return result


def _run_hostile(cmd, env=None):
    completed = run_command(
        cmd,
        capture_output=True,
        env=env,
        text=True,
    )
    return completed.stdout


def _copy_fetched_index(name, aligner, cache_dir, output_dir):
    cache_dir = Path(cache_dir)
    output_dir = Path(output_dir)
    copied = []

    if aligner in ("both", "minimap2"):
        copied.extend(
            _copy_matching_files(
                cache_dir,
                output_dir,
                [f"{name}.fa.gz", f"{name}.mmi"],
            )
        )
    if aligner in ("both", "bowtie2"):
        copied.extend(
            _copy_matching_files(
                cache_dir,
                output_dir,
                sorted(path.name for path in cache_dir.glob(f"{name}.*.bt2*")),
            )
        )

    if not copied:
        raise FileNotFoundError(f"Hostile did not fetch any index files for {name!r}.")


def _copy_matching_files(source_dir, output_dir, filenames):
    copied = []
    for filename in filenames:
        source = Path(source_dir, filename)
        if source.is_file():
            shutil.copyfile(source, Path(output_dir, filename))
            copied.append(filename)
    return copied
