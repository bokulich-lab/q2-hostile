from qiime2.plugin import Citations, Plugin
from q2_types.feature_table import FeatureTable, Frequency

from q2_hostile import __version__
from q2_hostile._methods import duplicate_table

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

plugin.methods.register_function(
    function=duplicate_table,
    inputs={'table': FeatureTable[Frequency]},
    parameters={},
    outputs=[('new_table', FeatureTable[Frequency])],
    input_descriptions={'table': 'The feature table to be duplicated.'},
    parameter_descriptions={},
    output_descriptions={'new_table': 'The duplicated feature table.'},
    name='Duplicate table',
    description=("Create a copy of a feature table with a new uuid. "
                 "This is for demonstration purposes only."),
    citations=[],
)
