import shutil
import tempfile
from pathlib import Path

from q2_hostile._types import HostileIndex
from qiime2 import Artifact
from qiime2.core.exceptions import ValidationError
from qiime2.plugin.testing import TestPluginBase

from q2_hostile._formats import HostileIndexDirFmt, HostileIndexMetadataFormat
from q2_hostile.plugin_setup import plugin


class TestHostileIndexFormats(TestPluginBase):
    package = "q2_hostile.tests"

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.tempdir_path = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def _copy_fixture_dir(self, fixture_path):
        destination = self.tempdir_path / Path(fixture_path).name
        shutil.copytree(self.get_data_path(fixture_path), destination)
        return destination

    def _assert_directory_format_valid(self, fixture_path, expected_files):
        index_dir = self._copy_fixture_dir(fixture_path)

        observed = HostileIndexDirFmt(str(index_dir), mode="r")
        observed.validate()

        self.assertEqual(
            sorted(path.name for path in index_dir.iterdir()),
            sorted(expected_files),
        )

    def test_metadata_format_accepts_required_fields(self):
        index_dir = self._copy_fixture_dir("semantic_formats/minimap2-index")

        observed = HostileIndexMetadataFormat(
            str(index_dir / "index.json"),
            mode="r",
        )

        observed.validate()

    def test_metadata_format_rejects_missing_required_fields(self):
        index_dir = self._copy_fixture_dir("semantic_formats/minimap2-index")
        (index_dir / "index.json").write_text('{"name": "human-t2t-hla"}')

        observed = HostileIndexMetadataFormat(
            str(index_dir / "index.json"),
            mode="r",
        )

        with self.assertRaisesRegex(
            ValueError,
            "Hostile index metadata is missing: aligner",
        ):
            observed.validate()

    def test_directory_format_requires_metadata_file(self):
        index_dir = self._copy_fixture_dir("semantic_formats/minimap2-index")
        (index_dir / "index.json").unlink()

        observed = HostileIndexDirFmt(str(index_dir), mode="r")

        with self.assertRaisesRegex(
            ValidationError,
            "Missing one or more files for HostileIndexDirFmt: 'index.json'",
        ):
            observed.validate()

    def test_directory_format_rejects_unrecognized_index_files(self):
        index_dir = self._copy_fixture_dir("semantic_formats/minimap2-index")
        (index_dir / "notes.txt").write_text("not an index")

        observed = HostileIndexDirFmt(str(index_dir), mode="r")

        with self.assertRaisesRegex(
            ValidationError,
            "Unrecognized file",
        ):
            observed.validate()

    def test_directory_format_accepts_minimap2_index_files(self):
        self._assert_directory_format_valid(
            "semantic_formats/minimap2-index",
            ["human-t2t-hla.fa.gz", "human-t2t-hla.mmi", "index.json"],
        )

    def test_directory_format_accepts_bowtie2_index_files(self):
        self._assert_directory_format_valid(
            "semantic_formats/bowtie2-index",
            [
                "human-t2t-hla.1.bt2",
                "human-t2t-hla.2.bt2",
                "human-t2t-hla.3.bt2",
                "human-t2t-hla.4.bt2",
                "human-t2t-hla.rev.1.bt2",
                "human-t2t-hla.rev.2.bt2",
                "index.json",
            ],
        )

    def test_directory_format_accepts_combined_index_files(self):
        self._assert_directory_format_valid(
            "semantic_formats/combined-index",
            [
                "human-t2t-hla.1.bt2",
                "human-t2t-hla.2.bt2",
                "human-t2t-hla.3.bt2",
                "human-t2t-hla.4.bt2",
                "human-t2t-hla.fa.gz",
                "human-t2t-hla.mmi",
                "human-t2t-hla.rev.1.bt2",
                "human-t2t-hla.rev.2.bt2",
                "index.json",
            ],
        )


class TestHostileIndexSemanticType(TestPluginBase):
    package = "q2_hostile.tests"

    def _assert_artifact_import_valid(self, fixture_path, expected_files):
        artifact = Artifact.import_data(
            "HostileIndex",
            self.get_data_path(fixture_path),
        )

        observed = artifact.view(HostileIndexDirFmt)

        self.assertEqual(str(artifact.type), "HostileIndex")
        self.assertEqual(
            sorted(path.name for path in Path(observed.path).iterdir()),
            sorted(expected_files),
        )

    def test_db_semantic_type_registration(self):
        self.assertRegisteredSemanticType(HostileIndex)

    def test_index_semantic_type_to_format_registration(self):
        self.assertSemanticTypeRegisteredToFormat(HostileIndex, HostileIndexDirFmt)

    def test_import_data_accepts_minimap2_index(self):
        self._assert_artifact_import_valid(
            "semantic_formats/minimap2-index",
            ["human-t2t-hla.fa.gz", "human-t2t-hla.mmi", "index.json"],
        )

    def test_import_data_accepts_bowtie2_index(self):
        self._assert_artifact_import_valid(
            "semantic_formats/bowtie2-index",
            [
                "human-t2t-hla.1.bt2",
                "human-t2t-hla.2.bt2",
                "human-t2t-hla.3.bt2",
                "human-t2t-hla.4.bt2",
                "human-t2t-hla.rev.1.bt2",
                "human-t2t-hla.rev.2.bt2",
                "index.json",
            ],
        )

    def test_import_data_accepts_combined_index(self):
        self._assert_artifact_import_valid(
            "semantic_formats/combined-index",
            [
                "human-t2t-hla.1.bt2",
                "human-t2t-hla.2.bt2",
                "human-t2t-hla.3.bt2",
                "human-t2t-hla.4.bt2",
                "human-t2t-hla.fa.gz",
                "human-t2t-hla.mmi",
                "human-t2t-hla.rev.1.bt2",
                "human-t2t-hla.rev.2.bt2",
                "index.json",
            ],
        )
