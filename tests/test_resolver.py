from n0conflict.resolver import ResolutionResult, _parse_response


class TestParseResponse:
    def test_resolved(self):
        text = "RESOLVED:\nreturn f'Hello, {name}!'\n"
        result = _parse_response(text)
        assert result.resolved is True
        assert "Hello" in result.content

    def test_cannot_resolve(self):
        text = (
            "CANNOT_RESOLVE:\n"
            "Both sides delete the same function but replace it with incompatible logic."
        )
        result = _parse_response(text)
        assert result.resolved is False
        assert "incompatible" in result.explanation

    def test_resolved_strips_whitespace(self):
        result = _parse_response("RESOLVED:\n\n   x = 1\n\n")
        assert result.content == "x = 1"

    def test_fallback_treats_raw_text_as_resolved(self):
        result = _parse_response("some raw code here")
        assert result.resolved is True
        assert result.content == "some raw code here"
