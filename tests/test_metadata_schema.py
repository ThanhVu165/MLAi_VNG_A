"""Schema quản trị nguồn phải chuyển được bằng SDK Gemini thật, không cần mạng."""

from google.generativeai.types.generation_types import to_generation_config_dict

from corpus.metadata import METADATA_SCHEMA


def test_metadata_schema_converts_with_real_gemini_sdk_offline() -> None:
    config = to_generation_config_dict({"response_schema": METADATA_SCHEMA})
    schema = config["response_schema"]
    assert list(schema.properties["status"].enum) == ["PENDING_REVIEW"]
    for name in schema.required:
        if name != "status":
            assert schema.properties[name].nullable
    assert schema.properties["domains"].items.type_.name == "STRING"
