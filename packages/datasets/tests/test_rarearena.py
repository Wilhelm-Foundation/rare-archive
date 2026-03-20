"""Tests for RareArena JSONL ingestion pipeline."""

import json

import pytest

from rare_archive_datasets.ingestion.rarearena import (
    RareArenaCase,
    compute_statistics,
    export_for_training,
    ingest_split,
    load_jsonl,
    parse_case,
)


class TestLoadJsonl:
    def test_valid_lines(self, tmp_path):
        f = tmp_path / "data.jsonl"
        f.write_text('{"a":1}\n{"b":2}\n')
        records = list(load_jsonl(f))
        assert records == [{"a": 1}, {"b": 2}]

    def test_blank_lines_skipped(self, tmp_path):
        f = tmp_path / "data.jsonl"
        f.write_text('{"a":1}\n\n\n{"b":2}\n')
        records = list(load_jsonl(f))
        assert len(records) == 2

    def test_malformed_json_skipped(self, tmp_path):
        f = tmp_path / "data.jsonl"
        f.write_text('{"a":1}\nnot json\n{"b":2}\n')
        records = list(load_jsonl(f))
        assert len(records) == 2

    def test_empty_file(self, tmp_path):
        f = tmp_path / "data.jsonl"
        f.write_text("")
        records = list(load_jsonl(f))
        assert records == []


class TestParseCase:
    def test_v1_format(self):
        record = {
            "input": "Patient presents with tall stature.",
            "output": "Marfan syndrome",
            "disease_id": "ORPHA:558",
        }
        case = parse_case(record, "rds")
        assert case.clinical_vignette == "Patient presents with tall stature."
        assert case.ground_truth_diagnosis == "Marfan syndrome"
        assert case.disease_id == "ORPHA:558"

    def test_v2_format(self):
        record = {
            "clinical_note": "A 5-year-old girl with renal failure.",
            "diagnosis": "Fabry disease",
            "orpha_code": "ORPHA:324",
        }
        case = parse_case(record, "rdc")
        assert case.clinical_vignette == "A 5-year-old girl with renal failure."
        assert case.ground_truth_diagnosis == "Fabry disease"
        assert case.disease_id == "ORPHA:324"

    def test_hpo_csv_string_to_list(self):
        record = {"input": "test", "output": "diag", "hpo_terms": "HP:0001250, HP:0001252"}
        case = parse_case(record, "rds")
        assert case.hpo_terms == ["HP:0001250", "HP:0001252"]

    def test_hpo_list_passthrough(self):
        record = {"input": "test", "output": "diag", "hpo_terms": ["HP:0001250", "HP:0001252"]}
        case = parse_case(record, "rds")
        assert case.hpo_terms == ["HP:0001250", "HP:0001252"]

    def test_auto_generated_case_id(self):
        record = {"input": "test", "output": "diag"}
        case = parse_case(record, "rds")
        assert case.case_id.startswith("rds_")

    def test_raw_data_preserved(self):
        record = {"input": "test", "output": "diag", "extra": "value"}
        case = parse_case(record, "rds")
        assert case.raw_data == record
        assert case.raw_data["extra"] == "value"


class TestIngestSplit:
    def test_ingests_all(self, tmp_path):
        f = tmp_path / "data.jsonl"
        records = [{"input": f"case{i}", "output": f"diag{i}"} for i in range(5)]
        f.write_text("\n".join(json.dumps(r) for r in records))
        cases = ingest_split(f, "rds")
        assert len(cases) == 5

    def test_max_cases_limit(self, tmp_path):
        f = tmp_path / "data.jsonl"
        records = [{"input": f"case{i}", "output": f"diag{i}"} for i in range(10)]
        f.write_text("\n".join(json.dumps(r) for r in records))
        cases = ingest_split(f, "rds", max_cases=3)
        assert len(cases) == 3

    def test_split_assigned(self, tmp_path):
        f = tmp_path / "data.jsonl"
        f.write_text('{"input":"test","output":"diag"}\n')
        cases = ingest_split(f, "rdc")
        assert all(c.split == "rdc" for c in cases)


class TestExportForTraining:
    def test_chat_format(self, tmp_path):
        cases = [
            RareArenaCase(
                case_id="1",
                clinical_vignette="vignette text",
                ground_truth_diagnosis="diagnosis text",
            )
        ]
        out = tmp_path / "out.jsonl"
        count = export_for_training(cases, out, format="chat")
        assert count == 1
        record = json.loads(out.read_text().strip())
        messages = record["messages"]
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

    def test_completion_format(self, tmp_path):
        cases = [
            RareArenaCase(
                case_id="1",
                clinical_vignette="vignette",
                ground_truth_diagnosis="diag",
            )
        ]
        out = tmp_path / "out.jsonl"
        count = export_for_training(cases, out, format="completion")
        assert count == 1
        record = json.loads(out.read_text().strip())
        assert "prompt" in record
        assert "completion" in record

    def test_skips_empty_vignettes(self, tmp_path):
        cases = [
            RareArenaCase(case_id="1", clinical_vignette="", ground_truth_diagnosis="diag"),
            RareArenaCase(case_id="2", clinical_vignette="vignette", ground_truth_diagnosis=""),
        ]
        out = tmp_path / "out.jsonl"
        count = export_for_training(cases, out)
        assert count == 0

    def test_returns_count(self, tmp_path):
        cases = [
            RareArenaCase(
                case_id=str(i),
                clinical_vignette=f"v{i}",
                ground_truth_diagnosis=f"d{i}",
            )
            for i in range(5)
        ]
        out = tmp_path / "out.jsonl"
        count = export_for_training(cases, out)
        assert count == 5


class TestComputeStatistics:
    def test_total_cases(self):
        cases = [
            RareArenaCase(case_id=str(i), clinical_vignette="v", ground_truth_diagnosis="d")
            for i in range(3)
        ]
        stats = compute_statistics(cases)
        assert stats["total_cases"] == 3

    def test_unique_diseases(self):
        cases = [
            RareArenaCase(case_id="1", clinical_vignette="v", ground_truth_diagnosis="Marfan"),
            RareArenaCase(case_id="2", clinical_vignette="v", ground_truth_diagnosis="Fabry"),
            RareArenaCase(case_id="3", clinical_vignette="v", ground_truth_diagnosis="Marfan"),
        ]
        stats = compute_statistics(cases)
        assert stats["unique_diseases"] == 2

    def test_cases_with_hpo(self):
        cases = [
            RareArenaCase(
                case_id="1", clinical_vignette="v", ground_truth_diagnosis="d",
                hpo_terms=["HP:0001250"],
            ),
            RareArenaCase(case_id="2", clinical_vignette="v", ground_truth_diagnosis="d"),
        ]
        stats = compute_statistics(cases)
        assert stats["cases_with_hpo"] == 1

    def test_split_distribution(self):
        cases = [
            RareArenaCase(
                case_id="1", clinical_vignette="v", ground_truth_diagnosis="d", split="rds",
            ),
            RareArenaCase(
                case_id="2", clinical_vignette="v", ground_truth_diagnosis="d", split="rds",
            ),
            RareArenaCase(
                case_id="3", clinical_vignette="v", ground_truth_diagnosis="d", split="rdc",
            ),
        ]
        stats = compute_statistics(cases)
        assert stats["split_distribution"] == {"rds": 2, "rdc": 1}
