import unittest

from llm_client import FALLBACK_DSL, generate_lockscreen_dsl, parse_model_json


class ModelJsonParsingTests(unittest.TestCase):
    def test_parses_json_from_markdown_wrapped_response(self):
        content = """Here is the result:
```json
{"version":"1.0","canvas":{"width":390,"height":844},"layers":[]}
```"""

        parsed = parse_model_json(content)

        self.assertEqual(parsed["canvas"], {"width": 390, "height": 844})

    def test_extracts_balanced_json_object_from_surrounding_text(self):
        content = 'Result: {"version":"1.0","layers":[{"content":"a {brace}"}]} done'

        parsed = parse_model_json(content)

        self.assertEqual(parsed["layers"][0]["content"], "a {brace}")


class FallbackTests(unittest.TestCase):
    def test_returns_fallback_when_request_fails(self):
        def failing_request(*args, **kwargs):
            raise RuntimeError("network unavailable")

        result = generate_lockscreen_dsl("night sky", requester=failing_request)

        self.assertEqual(result, FALLBACK_DSL)
        self.assertIsNot(result, FALLBACK_DSL)


if __name__ == "__main__":
    unittest.main()
