import json

from qiime2.plugin import model


class HostileIndexMetadataFormat(model.TextFileFormat):
    def _validate_(self, level):
        with self.open() as fh:
            metadata = json.load(fh)

        required = {'name', 'aligner'}
        missing = required - metadata.keys()
        if missing:
            raise ValueError(
                'Hostile index metadata is missing: '
                f'{", ".join(sorted(missing))}'
            )


class HostileIndexDirFmt(model.DirectoryFormat):
    index = model.File('index.json', format=HostileIndexMetadataFormat)
