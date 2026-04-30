# flake8: noqa
# ----------------------------------------------------------------------------
# Copyright (c) 2026, Bokulich Lab.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file LICENSE, distributed with this software.
# ----------------------------------------------------------------------------

import json
from pathlib import Path
import shutil
import tempfile

from q2_types.per_sample_sequences import (
    CasavaOneEightSingleLanePerSampleDirFmt,
)

from q2_hostile._formats import HostileIndexDirFmt, HostileIndexMetadataFormat
from q2_hostile._utils import run_command


def filter_reads(
    reads: CasavaOneEightSingleLanePerSampleDirFmt,
    index: HostileIndexDirFmt,
    aligner: str = "auto",
    threads: int = 1,
    invert: bool = False,
    rename: bool = False,
    reorder: bool = False,
) -> CasavaOneEightSingleLanePerSampleDirFmt:
    """Filter host-matching reads from a per-sample FASTQ directory."""
    index_metadata = _read_index_metadata(index)
    samples = reads.manifest
    paired = _is_paired(samples)
    effective_aligner = _resolve_aligner(aligner, paired)
    _validate_index_aligner(index_metadata["aligner"], effective_aligner)
    index_path = _index_path(index, index_metadata["name"], effective_aligner)

    result = CasavaOneEightSingleLanePerSampleDirFmt()

    with tempfile.TemporaryDirectory(prefix="q2-hostile-clean-") as tmpdir:
        tmpdir = Path(tmpdir)

        for sample_id, sample in samples.iterrows():
            sample_output = tmpdir / str(sample_id)
            sample_output.mkdir()
            cmd = _build_clean_command(
                fastq1=sample["forward"],
                fastq2=sample["reverse"] if paired else None,
                output_dir=sample_output,
                index=index_path,
                aligner=aligner,
                threads=threads,
                invert=invert,
                rename=rename,
                reorder=reorder,
            )
            _run_hostile(cmd)

            shutil.copyfile(
                _hostile_output_path(
                    sample_output,
                    sample["forward"],
                    paired=paired,
                    read_number=1,
                ),
                Path(result.path, Path(sample["forward"]).name),
            )
            if paired:
                shutil.copyfile(
                    _hostile_output_path(
                        sample_output,
                        sample["reverse"],
                        paired=paired,
                        read_number=2,
                    ),
                    Path(result.path, Path(sample["reverse"]).name),
                )

    return result


def _run_hostile(cmd, env=None):
    """Run a Hostile command and return its stdout."""
    completed = run_command(
        cmd,
        capture_output=True,
        env=env,
        text=True,
    )
    return completed.stdout


def _read_index_metadata(index):
    """Load the metadata stored in a Hostile index artifact."""
    with index.index.view(HostileIndexMetadataFormat).open() as fh:
        return json.load(fh)


def _is_paired(samples):
    """Return whether the manifest contains any paired-end reads."""
    return "reverse" in samples and samples["reverse"].notna().any()


def _resolve_aligner(aligner, paired):
    """Resolve the effective aligner to use for the current read layout."""
    if aligner != "auto":
        return aligner
    return "bowtie2" if paired else "minimap2"


def _validate_index_aligner(index_aligner, requested_aligner):
    """Ensure the fetched index contains files for the requested aligner."""
    if index_aligner == "both":
        return

    if index_aligner != requested_aligner:
        raise ValueError(
            f"The fetched index contains {index_aligner} files, but this "
            f"filtering run requires {requested_aligner}. Fetch the index "
            'again with aligner="both" or the required aligner.'
        )


def _index_path(index, name, aligner):
    """Return the Hostile index path prefix or FASTA path for an aligner."""
    index_dir = Path(index.path)
    if aligner == "bowtie2":
        path = index_dir / name
        required_path = Path(f"{path}.1.bt2")
    else:
        path = index_dir / f"{name}.fa.gz"
        required_path = path

    if not required_path.is_file():
        raise FileNotFoundError(
            f"The Hostile index artifact does not contain the {aligner} "
            f"index files for {name!r}."
        )

    return str(path)


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
    """Build the Hostile clean command for one sample."""
    cmd = [
        "hostile",
        "clean",
        "--fastq1",
        str(fastq1),
        "--index",
        index,
        "--aligner",
        aligner,
        "--threads",
        str(threads),
        "--output",
        str(output_dir),
        "--force",
        "--airplane",
    ]

    if fastq2 is not None:
        cmd.extend(["--fastq2", str(fastq2)])
    if invert:
        cmd.append("--invert")
    if rename:
        cmd.append("--rename")
    if reorder:
        cmd.append("--reorder")

    return cmd


def _hostile_output_path(output_dir, fastq, paired, read_number):
    """Map an input FASTQ name to the cleaned FASTQ emitted by Hostile."""
    stem = _fastq_path_to_stem(fastq)
    if not paired:
        suffix = ".clean.fastq.gz"
    elif read_number == 1:
        suffix = ".clean_1.fastq.gz"
    else:
        suffix = ".clean_2.fastq.gz"
    return Path(output_dir, f"{stem}{suffix}")


def _fastq_path_to_stem(fastq):
    """Strip FASTQ compression and sequence-file suffixes from a path."""
    stem = Path(fastq).name.removesuffix(".gz")
    for suffix in (".fastq", ".fq"):
        stem = stem.removesuffix(suffix)
    return stem
