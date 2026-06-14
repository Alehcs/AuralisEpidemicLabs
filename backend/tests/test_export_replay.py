"""Local run export and replay loader tests."""

from pathlib import Path

from app.infrastructure.exporters import RUN_FILES, ReplayLoader, RunExporter


def test_export_creates_expected_files_and_replay_reads_them(
    engine_factory,
    tmp_path: Path,
) -> None:
    engine = engine_factory(seed=77, simulation_id="export-test")
    engine.run(3)

    result = RunExporter(tmp_path).export(engine.state)

    run_directory = tmp_path / "runs" / "export-test"
    assert result["run_id"] == "export-test"
    assert all((run_directory / filename).is_file() for filename in RUN_FILES)

    replay = ReplayLoader(tmp_path)
    assert replay.metadata("export-test")["seed"] == 77
    snapshots = replay.snapshots("export-test")
    assert [item["tick"] for item in snapshots] == [0, 1, 2, 3]
    assert replay.list_runs()[0]["run_id"] == "export-test"
