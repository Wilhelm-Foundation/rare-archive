"""Tests for rare_archive_ontology.schemas — JSON schema validation."""

from rare_archive_ontology.schemas import (
    _SCHEMA_CACHE,
    _load_schema,
    validate_clinical_tool,
    validate_context_file,
    validate_dataset,
    validate_model,
    validate_patient_category,
)


class TestLoadSchema:
    def test_returns_dict(self):
        schema = _load_schema("patient_category")
        assert isinstance(schema, dict)
        assert schema["title"] == "Patient Category"

    def test_caching(self):
        _SCHEMA_CACHE.pop("patient_category", None)
        first = _load_schema("patient_category")
        second = _load_schema("patient_category")
        assert first is second

    def test_missing_schema_raises(self):
        import pytest

        with pytest.raises(FileNotFoundError):
            _load_schema("nonexistent_domain")


class TestValidatePatientCategory:
    def test_valid(self, valid_patient_category):
        errors = validate_patient_category(valid_patient_category)
        assert errors == []

    def test_missing_required_fields(self):
        errors = validate_patient_category({})
        assert len(errors) > 0
        field_names = " ".join(errors)
        for field in ("category_id", "name", "version", "diseases", "phenotypic_features"):
            assert field in field_names

    def test_invalid_category_id_pattern(self, valid_patient_category):
        data = {**valid_patient_category, "category_id": "BAD-ID"}
        errors = validate_patient_category(data)
        assert any("does not match" in e for e in errors)

    def test_invalid_version_format(self, valid_patient_category):
        data = {**valid_patient_category, "version": "not-semver"}
        errors = validate_patient_category(data)
        assert len(errors) > 0


class TestValidateClinicalTool:
    def test_valid(self, valid_clinical_tool):
        errors = validate_clinical_tool(valid_clinical_tool)
        assert errors == []

    def test_missing_required_fields(self):
        errors = validate_clinical_tool({})
        assert len(errors) > 0
        field_names = " ".join(errors)
        for field in ("tool_id", "name", "version", "api"):
            assert field in field_names

    def test_missing_api_subfields(self, valid_clinical_tool):
        data = {**valid_clinical_tool, "api": {}}
        errors = validate_clinical_tool(data)
        assert len(errors) > 0


class TestValidateModel:
    def test_valid(self, valid_model):
        errors = validate_model(valid_model)
        assert errors == []

    def test_missing_required_fields(self):
        errors = validate_model({})
        assert len(errors) > 0
        field_names = " ".join(errors)
        for field in ("model_id", "name", "version", "base_model", "training_stage"):
            assert field in field_names

    def test_invalid_architecture_enum(self, valid_model):
        data = {**valid_model, "base_model": {**valid_model["base_model"], "architecture": "transformer"}}
        errors = validate_model(data)
        assert len(errors) > 0


class TestValidateDataset:
    def test_valid(self, valid_dataset):
        errors = validate_dataset(valid_dataset)
        assert errors == []

    def test_missing_required_fields(self):
        errors = validate_dataset({})
        assert len(errors) > 0
        field_names = " ".join(errors)
        for field in ("dataset_id", "name", "version", "dataset_type", "license"):
            assert field in field_names

    def test_invalid_dataset_type_enum(self, valid_dataset):
        data = {**valid_dataset, "dataset_type": "invalid_type"}
        errors = validate_dataset(data)
        assert len(errors) > 0


class TestValidateContextFile:
    def test_valid(self, valid_context_file):
        errors = validate_context_file(valid_context_file)
        assert errors == []

    def test_missing_required_fields(self):
        errors = validate_context_file({})
        assert len(errors) > 0
        field_names = " ".join(errors)
        for field in ("context_id", "title", "version", "category", "description", "when_to_use"):
            assert field in field_names

    def test_invalid_context_id_pattern(self, valid_context_file):
        data = {**valid_context_file, "context_id": "BAD-ID"}
        errors = validate_context_file(data)
        assert any("does not match" in e for e in errors)

    def test_invalid_category_enum(self, valid_context_file):
        data = {**valid_context_file, "category": "invalid_category"}
        errors = validate_context_file(data)
        assert len(errors) > 0

    def test_description_min_length(self, valid_context_file):
        data = {**valid_context_file, "description": "too short"}
        errors = validate_context_file(data)
        assert len(errors) > 0

    def test_invalid_tool_id_in_connections(self, valid_context_file):
        data = {
            **valid_context_file,
            "tool_connections": [{"tool_id": "INVALID", "role": "test"}],
        }
        errors = validate_context_file(data)
        assert any("does not match" in e for e in errors)

    def test_all_categories_accepted(self, valid_context_file):
        for cat in [
            "diagnostic_workflow",
            "interpretation_guide",
            "data_source_guide",
            "tool_sequence",
            "phenotype_pattern",
            "diagnostic_odyssey",
        ]:
            data = {**valid_context_file, "category": cat}
            errors = validate_context_file(data)
            assert errors == [], f"Category '{cat}' should be valid but got: {errors}"
