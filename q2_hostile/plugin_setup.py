from qiime2.plugin import Bool, Choices, Citations, Int, Plugin, Range, Str
from qiime2.core.type import TypeMatch
from q2_types.per_sample_sequences import (
    PairedEndSequencesWithQuality,
    SequencesWithQuality,
)
from q2_types.sample_data import SampleData

from q2_hostile import __version__
from q2_hostile._formats import (
    HostileIndexDirFmt,
    HostileIndexFileFormat,
    HostileIndexMetadataFormat,
)
from q2_hostile.filter import filter_reads
from q2_hostile.index import fetch_index
from q2_hostile._types import HostileIndex

citations = Citations.load("citations.bib", package="q2_hostile")
READS = TypeMatch([SequencesWithQuality, PairedEndSequencesWithQuality])

plugin = Plugin(
    name="hostile",
    version=__version__,
    website="https://github.com/bede/hostile",
    package="q2_hostile",
    description="Remove host reads from sequence data with Hostile.",
    short_description="Host read removal with Hostile.",
    citations=[citations['Caporaso-Bolyen-2024']],
)

plugin.register_formats(
    HostileIndexFileFormat,
    HostileIndexMetadataFormat,
    HostileIndexDirFmt,
)

plugin.register_semantic_types(HostileIndex)

plugin.register_artifact_class(
    HostileIndex,
    directory_format=HostileIndexDirFmt,
    description='A downloaded standard Hostile index.',
)

plugin.methods.register_function(
    function=fetch_index,
    inputs={},
    parameters={
        'name': Str,
        'aligner': Str % Choices('both', 'minimap2', 'bowtie2'),
    },
    outputs=[('index', HostileIndex)],
    input_descriptions={},
    parameter_descriptions={
        'name': 'Name of a standard Hostile index to download.',
        'aligner': (
            'Index flavor to fetch. Use "both" to fetch both Minimap2 and '
            'Bowtie2 indexes when available.'
        ),
    },
    output_descriptions={
        'index': 'The downloaded Hostile index files.',
    },
    name='Fetch index',
    description=(
        'Download and cache a standard Hostile index for later host read '
        'filtering.'
    ),
    citations=[citations['Constantinides-Hunt-Crook-2023']],
)

plugin.methods.register_function(
    function=filter_reads,
    inputs={
        'reads': SampleData[READS],
        'index': HostileIndex,
    },
    parameters={
        'aligner': Str % Choices('auto', 'minimap2', 'bowtie2'),
        'threads': Int % Range(1, None),
        'invert': Bool,
        'rename': Bool,
        'reorder': Bool,
    },
    outputs=[('filtered_reads', SampleData[READS])],
    input_descriptions={
        'reads': 'Single- or paired-end reads to filter.',
        'index': 'A Hostile index artifact produced by fetch-index.',
    },
    parameter_descriptions={
        'aligner': (
            'Alignment algorithm to use. Hostile uses Minimap2 for single-end '
            'reads and Bowtie2 for paired-end reads when set to "auto".'
        ),
        'threads': 'Number of alignment threads.',
        'invert': 'Keep only reads aligning to the index.',
        'rename': 'Replace read names with incrementing integers.',
        'reorder': 'Ensure deterministic output order.',
    },
    output_descriptions={
        'filtered_reads': 'Reads remaining after Hostile filtering.',
    },
    name='Filter reads',
    description=(
        'Remove reads that align to a fetched Hostile index from single- or '
        'paired-end sequence data.'
    ),
    citations=[citations['Constantinides-Hunt-Crook-2023']],
)
