import unittest
from unittest.mock import patch

from llm_client import (
    FALLBACK_DSL,
    generate_lockscreen_dsl,
    normalize_dsl,
    parse_model_json,
)


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


class AssetDslTests(unittest.TestCase):
    def test_normalize_asset_layer_uses_catalog_source(self):
        result = normalize_dsl(
            {
                "layers": [
                    {
                        "id": "rocket",
                        "type": "asset",
                        "assetId": "doodle-034",
                        "src": "https://untrusted.example/rocket.svg",
                        "x": 72,
                        "y": 340,
                        "width": 246,
                        "height": 246,
                    }
                ]
            }
        )

        self.assertEqual(result["layers"][0]["src"], "/materials/svg/doodle-34.svg")

    def test_normalize_drops_unknown_asset(self):
        with self.assertRaises(ValueError):
            normalize_dsl(
                {
                    "layers": [
                        {
                            "id": "unknown",
                            "type": "asset",
                            "assetId": "not-in-catalog",
                        }
                    ]
                }
            )

    @patch.dict(
        "os.environ",
        {
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://example.test/v1",
            "LLM_MODEL": "test-model",
        },
        clear=False,
    )
    def test_generation_extracts_slots_then_composes_with_candidates(self):
        class FakeResponse:
            def __init__(self, content):
                self.content = content

            def raise_for_status(self):
                return None

            def json(self):
                return {"choices": [{"message": {"content": self.content}}]}

        responses = iter(
            [
                FakeResponse(
                    """
                    {
                      "theme": "space",
                      "moods": ["cute"],
                      "colors": ["blue"],
                      "assetSlots": [{
                        "slot": "hero",
                        "query": "cute space rocket",
                        "subjects": ["rocket"],
                        "themes": ["space"],
                        "roles": ["hero"],
                        "preferredPosition": "center"
                      }]
                    }
                    """
                ),
                FakeResponse(
                    """
                    {
                      "version": "1.0",
                      "canvas": {"width": 390, "height": 844},
                      "theme": "space",
                      "mode": "static",
                      "background": {
                        "type": "gradient",
                        "value": "linear-gradient(180deg, #172554 0%, #020617 100%)"
                      },
                      "layers": [{
                        "id": "hero-rocket",
                        "type": "asset",
                        "assetId": "doodle-034",
                        "src": "https://untrusted.example/rocket.svg",
                        "x": 70,
                        "y": 330,
                        "width": 250,
                        "height": 250
                      }]
                    }
                    """
                ),
            ]
        )
        payloads = []

        def requester(*args, **kwargs):
            payloads.append(kwargs["json"])
            return next(responses)

        result = generate_lockscreen_dsl("生成一个可爱的太空火箭锁屏", requester=requester)

        self.assertEqual(len(payloads), 2)
        self.assertIn("doodle-034", payloads[1]["messages"][1]["content"])
        self.assertEqual(result["layers"][0]["assetId"], "doodle-034")
        self.assertEqual(result["layers"][0]["src"], "/materials/svg/doodle-34.svg")


if __name__ == "__main__":
    unittest.main()
