from qiime2.plugin import Choices, Citations, Plugin, Str

from q2_hostile import __version__
from q2_hostile._formats import HostileIndexDirFmt, HostileIndexMetadataFormat
from q2_hostile._methods import fetch_index
from q2_hostile._types import HostileIndex

citations = Citations.load("citations.bib", package="q2_hostile")

plugin = Plugin(
    name="hostile",
    version=__version__,
    website="https://github.com/bede/hostile",
    package="q2_hostile",
    description="Remove host reads from sequence data with Hostile.",
    short_description="Host read removal with Hostile.",
    citations=[citations['Caporaso-Bolyen-2024']],
)

plugin.register_formats(HostileIndexMetadataFormat, HostileIndexDirFmt)

plugin.register_semantic_types(HostileIndex)

plugin.register_artifact_class(
    HostileIndex,
    directory_format=HostileIndexDirFmt,
    description='A standard Hostile index that has been downloaded locally.',
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
        'index': 'A record of the downloaded Hostile index.',
    },
    name='Fetch index',
    description=(
        'Download and cache a standard Hostile index for later host read '
        'filtering.'
    ),
    citations=[citations['Constantinides-Hunt-Crook-2023']],
)
