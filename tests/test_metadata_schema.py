"""Contract metadata và OpenAI schema normalization, không gọi mạng."""

from copy import deepcopy

from corpus.metadata import METADATA_SCHEMA
from infra.llm import _openai_schema


def test_metadata_schema_normalizes_for_openai_without_mutation() -> None:
    original = deepcopy(METADATA_SCHEMA)
    schema = _openai_schema(METADATA_SCHEMA)
    assert schema["properties"]["status"]["enum"] == ["PENDING_REVIEW"]
    for name in schema["required"]:
        if name != "status":
            assert schema["properties"][name]["nullable"] is True
    assert schema["properties"]["domains"]["items"]["type"] == "string"
    assert schema["additionalProperties"] is False
    assert "additionalProperties" not in METADATA_SCHEMA
    assert METADATA_SCHEMA == original
