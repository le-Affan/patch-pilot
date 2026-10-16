import pytest

from patchpilot.llm import parse_response


def test_plain_json():
    assert parse_response('{"diagnosis": "d", "fixed_code": "x=1"}') == {"diagnosis": "d", "fixed_code": "x=1"}


def test_fenced_json():
    out = parse_response('```json\n{"diagnosis": "d", "fixed_code": "x=1"}\n```')
    assert out["fixed_code"] == "x=1"


def test_extra_prose():
    out = parse_response('Sure! Here:\n{"diagnosis": "d", "fixed_code": "x=1"}\nHope it helps.')
    assert out["diagnosis"] == "d"


def test_think_block():
    out = parse_response('<think>{"fixed_code": "bad"}</think>{"diagnosis": "d", "fixed_code": "ok"}')
    assert out["fixed_code"] == "ok"


def test_missing_diagnosis():
    assert parse_response('{"fixed_code": "x=1"}') == {"diagnosis": "", "fixed_code": "x=1"}


def test_bare_code_fence_fallback():
    assert parse_response("```python\nprint(1)\n```")["fixed_code"].strip() == "print(1)"


def test_garbage_raises():
    with pytest.raises(ValueError):
        parse_response("no json here")
    with pytest.raises(ValueError):
        parse_response('{"diagnosis": "d"}')
