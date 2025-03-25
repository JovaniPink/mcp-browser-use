import pytest
import os
from mcp_browser_use.utils.utils import get_llm_model, encode_image


def test_encode_image(tmp_path):
    # Create a temporary image file
    img_file = tmp_path / "test.png"
    img_file.write_bytes(b"\x89PNG\r\n\x1a\n...")  # minimal PNG data
    encoded = encode_image(str(img_file))
    assert isinstance(encoded, str)
    assert "iVBOR" in encoded  # typical base64 PNG prefix


def test_get_llm_model_anthropic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-api-key")
    model = get_llm_model("anthropic", model_name="claude-instant")
    assert model.model_name == "claude-instant"
