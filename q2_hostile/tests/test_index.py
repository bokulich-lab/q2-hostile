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
import tempfile
from unittest.mock import MagicMock
from unittest.mock import patch

from qiime2.plugin.testing import TestPluginBase

from q2_hostile._formats import HostileIndexDirFmt
from q2_hostile.index import _copy_fetched_index, fetch_index


class TestFetchIndex(TestPluginBase):
    package = "q2_hostile.tests"

    def setUp(self):
        self.cache = tempfile.TemporaryDirectory()
        self.cache_dir = self.cache.name

    def tearDown(self):
        self.cache.cleanup()

    def _mock_tempdir(self):
        mock_tempdir = MagicMock()
        mock_tempdir.__enter__.return_value = self.cache_dir
        mock_tempdir.__exit__.return_value = None
        return mock_tempdir

    def _expected_env(self):
        return {"HOSTILE_CACHE_DIR": self.cache_dir}

    @patch("q2_hostile.index.os.environ.copy")
    @patch("q2_hostile.index.tempfile.TemporaryDirectory")
    @patch("q2_hostile.index._copy_fetched_index")
    @patch("q2_hostile.index._run_hostile")
    def test_fetch_index_runs_hostile_and_writes_metadata(
        self,
        mock_run_hostile,
        mock_copy_fetched_index,
        mock_temporary_directory,
        mock_environ_copy,
    ):
        mock_temporary_directory.return_value = self._mock_tempdir()
        mock_environ_copy.return_value = {}

        observed = fetch_index(name="human-t2t-hla", aligner="both")

        self.assertIsInstance(observed, HostileIndexDirFmt)

        metadata = json.loads(Path(observed.path, "index.json").read_text())
        self.assertEqual(metadata, {"name": "human-t2t-hla", "aligner": "both"})

        mock_run_hostile.assert_called_once_with(
            ["hostile", "index", "fetch", "--name", "human-t2t-hla"],
            env=self._expected_env(),
        )

        mock_copy_fetched_index.assert_called_once_with(
            "human-t2t-hla",
            "both",
            self.cache_dir,
            observed.path,
        )

    @patch("q2_hostile.index.os.environ.copy")
    @patch("q2_hostile.index.tempfile.TemporaryDirectory")
    @patch("q2_hostile.index._copy_fetched_index")
    @patch("q2_hostile.index._run_hostile")
    def test_fetch_index_requests_minimap2(
        self,
        mock_run_hostile,
        mock_copy_fetched_index,
        mock_temporary_directory,
        mock_environ_copy,
    ):
        mock_temporary_directory.return_value = self._mock_tempdir()
        mock_environ_copy.return_value = {}

        observed = fetch_index(name="human-t2t-hla", aligner="minimap2")

        mock_run_hostile.assert_called_once_with(
            ["hostile", "index", "fetch", "--name", "human-t2t-hla", "--minimap2"],
            env=self._expected_env(),
        )
        mock_copy_fetched_index.assert_called_once_with(
            "human-t2t-hla",
            "minimap2",
            self.cache_dir,
            observed.path,
        )

    @patch("q2_hostile.index.os.environ.copy")
    @patch("q2_hostile.index.tempfile.TemporaryDirectory")
    @patch("q2_hostile.index._copy_fetched_index")
    @patch("q2_hostile.index._run_hostile")
    def test_fetch_index_requests_bowtie2(
        self,
        mock_run_hostile,
        mock_copy_fetched_index,
        mock_temporary_directory,
        mock_environ_copy,
    ):
        mock_temporary_directory.return_value = self._mock_tempdir()
        mock_environ_copy.return_value = {}

        observed = fetch_index(name="human-t2t-hla", aligner="bowtie2")

        mock_run_hostile.assert_called_once_with(
            ["hostile", "index", "fetch", "--name", "human-t2t-hla", "--bowtie2"],
            env=self._expected_env(),
        )
        mock_copy_fetched_index.assert_called_once_with(
            "human-t2t-hla",
            "bowtie2",
            self.cache_dir,
            observed.path,
        )


class TestCopyFetchedIndex(TestPluginBase):
    package = "q2_hostile.tests"

    def setUp(self):
        self.cache = tempfile.TemporaryDirectory()
        self.output = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.cache.name)
        self.output_dir = Path(self.output.name)

    def tearDown(self):
        self.cache.cleanup()
        self.output.cleanup()

    def _write_cache_files(self, filenames):
        for filename in filenames:
            Path(self.cache_dir, filename).write_bytes(b"index")

    def _observed_output_files(self):
        return sorted(path.name for path in self.output_dir.iterdir())

    def test_copy_fetched_index_copies_both_index_families(self):
        self._write_cache_files(
            [
                "human-t2t-hla.fa.gz",
                "human-t2t-hla.mmi",
                "human-t2t-hla.1.bt2",
                "human-t2t-hla.2.bt2",
                "human-t2t-hla.3.bt2",
                "human-t2t-hla.4.bt2",
                "human-t2t-hla.rev.1.bt2",
                "human-t2t-hla.rev.2.bt2",
                "other.1.bt2",
            ]
        )

        _copy_fetched_index(
            "human-t2t-hla",
            "both",
            self.cache_dir,
            self.output_dir,
        )

        self.assertEqual(
            self._observed_output_files(),
            [
                "human-t2t-hla.1.bt2",
                "human-t2t-hla.2.bt2",
                "human-t2t-hla.3.bt2",
                "human-t2t-hla.4.bt2",
                "human-t2t-hla.fa.gz",
                "human-t2t-hla.mmi",
                "human-t2t-hla.rev.1.bt2",
                "human-t2t-hla.rev.2.bt2",
            ],
        )

    def test_copy_fetched_index_copies_minimap2_only(self):
        self._write_cache_files(
            [
                "human-t2t-hla.fa.gz",
                "human-t2t-hla.mmi",
                "human-t2t-hla.1.bt2",
            ]
        )

        _copy_fetched_index(
            "human-t2t-hla",
            "minimap2",
            self.cache_dir,
            self.output_dir,
        )

        self.assertEqual(
            self._observed_output_files(),
            [
                "human-t2t-hla.fa.gz",
                "human-t2t-hla.mmi",
            ],
        )

    def test_copy_fetched_index_copies_bowtie2_only(self):
        self._write_cache_files(
            [
                "human-t2t-hla.fa.gz",
                "human-t2t-hla.1.bt2",
                "human-t2t-hla.rev.2.bt2",
            ]
        )

        _copy_fetched_index(
            "human-t2t-hla",
            "bowtie2",
            self.cache_dir,
            self.output_dir,
        )

        self.assertEqual(
            self._observed_output_files(),
            [
                "human-t2t-hla.1.bt2",
                "human-t2t-hla.rev.2.bt2",
            ],
        )

    def test_copy_fetched_index_raises_when_nothing_matches(self):
        self._write_cache_files(["other.1.bt2"])

        with self.assertRaisesRegex(
            FileNotFoundError,
            "Hostile did not fetch any index files for 'missing-index'",
        ):
            _copy_fetched_index(
                "missing-index",
                "both",
                self.cache_dir,
                self.output_dir,
            )
