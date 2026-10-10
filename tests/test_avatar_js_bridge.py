import json

from desktop_study_companion.avatar.widget import decode_js_payload


def test_decode_js_payload_from_json_string() -> None:
    payload = json.dumps({"ready": "true", "error": ""})
    assert decode_js_payload(payload) == {
        "ready": "true",
        "error": "",
    }


def test_decode_js_payload_keeps_dict() -> None:
    value = {"ready": True, "webglLost": ""}
    assert decode_js_payload(value) == value


def test_decode_js_payload_rejects_invalid_or_empty_values() -> None:
    assert decode_js_payload("") == {}
    assert decode_js_payload("not-json") == {}
