import json

import pytest

from pycalendar.interface.core.generator import InterfaceGenerator
from pycalendar.interface import validate_structure as interface_validator


@pytest.mark.unit
def test_load_all_css_requires_manifest(tmp_path):
    """The CSS pipeline must fail loudly when manifest.json is absent."""
    generator = InterfaceGenerator()
    generator.assets_dir = tmp_path / "assets"
    styles_dir = generator.assets_dir / "styles"
    styles_dir.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="CSS manifest missing"):
        generator._load_all_css()


@pytest.mark.unit
def test_validate_structure_reports_missing_file(monkeypatch):
    """validate_structure should list every missing entry from EXPECTED_STRUCTURE."""
    sentinel_section = "__tests__"
    sentinel_file = "missing.txt"

    overridden = dict(interface_validator.EXPECTED_STRUCTURE)
    overridden[sentinel_section] = [sentinel_file]
    monkeypatch.setattr(interface_validator, "EXPECTED_STRUCTURE", overridden)

    _, missing = interface_validator.validate_structure()

    assert f"{sentinel_section}/{sentinel_file}" in missing


@pytest.mark.unit
def test_load_all_css_succeeds_with_manifest_and_preserves_order(tmp_path):
    """Generator should stitch CSS files following the manifest order without raising."""
    generator = InterfaceGenerator()
    generator.assets_dir = tmp_path / "assets"
    styles_dir = generator.assets_dir / "styles"
    base_dir = styles_dir / "base"
    components_dir = styles_dir / "components"

    for folder in (base_dir, components_dir):
        folder.mkdir(parents=True, exist_ok=True)

    manifest = [
        {"section": "Base", "files": ["base/reset.css", "base/layout.css"]},
        {"section": "Components", "files": ["components/buttons.css"]},
    ]
    (styles_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    css_files = [
        (base_dir / "reset.css", "body{--reset:1;}"),
        (base_dir / "layout.css", ".app{display:grid;}"),
        (components_dir / "buttons.css", ".btn{font-weight:600;}"),
    ]
    for path, content in css_files:
        path.write_text(content, encoding="utf-8")

    css_bundle = generator._load_all_css()

    markers = [
        "/* styles/base/reset.css */",
        "/* styles/base/layout.css */",
        "/* styles/components/buttons.css */",
    ]
    positions = [css_bundle.index(marker) for marker in markers]

    assert positions == sorted(positions)
    for snippet in ("--reset:1", "display:grid", "font-weight:600"):
        assert snippet in css_bundle
