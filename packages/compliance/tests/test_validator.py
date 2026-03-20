"""Tests for rare_archive_compliance.validator."""

from rare_archive_compliance.validator import (
    validate_adna_envelope,
    validate_adna_triad,
    validate_naming_convention,
)


class TestValidateAdnaEnvelope:
    def test_valid_envelope(self, valid_envelope):
        errors = validate_adna_envelope(valid_envelope)
        assert errors == []

    def test_empty_data(self):
        errors = validate_adna_envelope({})
        assert len(errors) > 0
        field_names = " ".join(errors)
        for field in ("name", "version", "type", "namespace", "triad"):
            assert field in field_names

    def test_invalid_name_pattern(self, valid_envelope):
        data = {**valid_envelope, "name": "Bad-Name"}
        errors = validate_adna_envelope(data)
        assert len(errors) > 0

    def test_invalid_type_enum(self, valid_envelope):
        data = {**valid_envelope, "type": "not_a_valid_type"}
        errors = validate_adna_envelope(data)
        assert len(errors) > 0

    def test_invalid_version_format(self, valid_envelope):
        data = {**valid_envelope, "version": "v1"}
        errors = validate_adna_envelope(data)
        assert len(errors) > 0

    def test_invalid_namespace(self, valid_envelope):
        data = {**valid_envelope, "namespace": "other_"}
        errors = validate_adna_envelope(data)
        assert len(errors) > 0


class TestValidateAdnaTriad:
    def test_valid_structure(self, adna_triad_repo):
        errors = validate_adna_triad(adna_triad_repo)
        assert errors == []

    def test_missing_agentic_dir(self, tmp_path):
        errors = validate_adna_triad(tmp_path)
        assert len(errors) == 1
        assert ".agentic/" in errors[0]

    def test_missing_triad_dirs(self, tmp_path):
        agentic = tmp_path / ".agentic"
        agentic.mkdir()
        (agentic / "AGENTS.md").write_text("# Agents")
        errors = validate_adna_triad(tmp_path)
        assert any(".agentic/what/" in e for e in errors)
        assert any(".agentic/how/" in e for e in errors)
        assert any(".agentic/who/" in e for e in errors)

    def test_missing_root_agents_md(self, tmp_path):
        agentic = tmp_path / ".agentic"
        agentic.mkdir()
        for leg in ("what", "how", "who"):
            d = agentic / leg
            d.mkdir()
            (d / "AGENTS.md").write_text(f"# {leg}")
        # No root AGENTS.md
        errors = validate_adna_triad(tmp_path)
        assert any("AGENTS.md" in e for e in errors)

    def test_missing_leg_agents_md(self, tmp_path):
        agentic = tmp_path / ".agentic"
        agentic.mkdir()
        (agentic / "AGENTS.md").write_text("# Agents")
        for leg in ("what", "how", "who"):
            (agentic / leg).mkdir()
            # Deliberately skip writing AGENTS.md inside legs
        errors = validate_adna_triad(tmp_path)
        assert len(errors) == 3  # one per leg


class TestValidateNamingConvention:
    def test_valid_file_name(self):
        errors = validate_naming_convention("patient_category.py", context="file")
        assert errors == []

    def test_file_name_with_hyphens(self):
        errors = validate_naming_convention("patient-category.py", context="file")
        assert len(errors) == 1
        assert "hyphens" in errors[0]

    def test_file_name_uppercase(self):
        errors = validate_naming_convention("MyFile.py", context="file")
        assert any("not lowercase" in e for e in errors)

    def test_valid_huggingface_name(self):
        errors = validate_naming_convention("rare-archive-model-v1", context="huggingface")
        assert errors == []

    def test_huggingface_name_with_underscores(self):
        errors = validate_naming_convention("rare_archive_model", context="huggingface")
        assert len(errors) == 1
        assert "underscores" in errors[0]

    def test_huggingface_name_uppercase(self):
        errors = validate_naming_convention("Rare-Archive", context="huggingface")
        assert any("not lowercase" in e for e in errors)
