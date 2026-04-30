import json

from qiime2.plugin import model


class HostileIndexFileFormat(model.BinaryFileFormat):
    def _validate_(self, level):
        pass


class HostileIndexMetadataFormat(model.TextFileFormat):
    def _validate_(self, level):
        with self.open() as fh:
            metadata = json.load(fh)

        required = {"name", "aligner"}
        missing = required - metadata.keys()
        if missing:
            raise ValueError(
                "Hostile index metadata is missing: " f'{", ".join(sorted(missing))}'
            )


class HostileIndexDirFmt(model.DirectoryFormat):
    index = model.File("index.json", format=HostileIndexMetadataFormat)
    files = model.FileCollection(
        (r".+\.(?:fa\.gz|mmi|(?:rev\.[12]|[1-4])\.bt2l?)$"),
        format=HostileIndexFileFormat,
    )

    @files.set_path_maker
    def files_path_maker(self, name):
        return str(name)
