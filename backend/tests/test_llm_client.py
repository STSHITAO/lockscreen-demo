import unittest
from unittest.mock import patch

from llm_client import (
    FALLBACK_DSL,
    generate_lockscreen_draft,
    generate_lockscreen_dsl,
    normalize_dsl,
    normalize_intent,
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

    def test_normalize_intent_keeps_controlled_animation_requirements(self):
        intent = normalize_intent(
            {
                "theme": "cute",
                "animationRequirements": [
                    {
                        "target": "heart",
                        "motion": "pulse",
                        "complexity": "simple",
                        "preferredPosition": "top-right",
                    },
                    {
                        "target": "castle",
                        "motion": "transform-and-fly",
                        "complexity": "complex",
                    },
                ],
            },
            "animated lockscreen",
        )

        assert intent["animationRequirements"] == [
            {
                "target": "heart",
                "motion": "pulse",
                "complexity": "simple",
                "preferredPosition": "top-right",
            },
            {
                "target": "castle",
                "motion": "transform-and-fly",
                "complexity": "complex",
                "preferredPosition": "center",
            },
        ]

    def test_normalize_intent_keeps_controlled_interaction_requirements(self):
        intent = normalize_intent(
            {
                "theme": "cute",
                "interactionRequirements": [
                    {
                        "target": "heart",
                        "trigger": {
                            "type": "multiTap",
                            "count": 5,
                            "withinMs": 1500,
                        },
                        "actions": [
                            {
                                "type": "animate",
                                "animation": "pulse",
                                "duration": 600,
                                "speed": 2,
                            },
                            {
                                "type": "burst",
                                "count": 14,
                                "afterEffect": "hide",
                            },
                        ],
                    }
                ],
            },
            "连续点击爱心五次后爆炸消失",
        )

        requirement = intent["interactionRequirements"][0]
        assert requirement["target"] == "heart"
        assert requirement["trigger"]["count"] == 5
        assert requirement["actions"][-1]["afterEffect"] == "hide"


class FallbackTests(unittest.TestCase):
    def test_returns_fallback_when_request_fails(self):
        def failing_request(*args, **kwargs):
            raise RuntimeError("network unavailable")

        result = generate_lockscreen_dsl("night sky", requester=failing_request)

        self.assertEqual(result["canvas"], FALLBACK_DSL["canvas"])
        self.assertEqual(result["background"], FALLBACK_DSL["background"])
        animation = next(
            layer
            for layer in result["layers"]
            if layer.get("type") == "frameAnimation"
        )
        self.assertEqual(animation["assetId"], "frame-star-twinkle-001")
        self.assertEqual(animation["fps"], 6)
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

    def test_normalize_frame_animation_uses_catalog_frames(self):
        result = normalize_dsl(
            {
                "layers": [
                    {
                        "id": "twinkle",
                        "type": "frameAnimation",
                        "assetId": "frame-star-twinkle-001",
                        "frames": ["https://untrusted.example/frame.png"],
                        "fps": 120,
                        "x": 280,
                        "y": 300,
                        "width": 80,
                        "height": 80,
                    }
                ]
            },
            allowed_asset_ids={"frame-star-twinkle-001"},
        )

        layer = result["layers"][0]
        self.assertEqual(layer["type"], "frameAnimation")
        self.assertEqual(layer["fps"], 6)
        self.assertEqual(len(layer["frames"]), 5)
        self.assertTrue(
            all(
                frame.startswith("/materials/frames/star_twinkle/")
                for frame in layer["frames"]
            )
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

    @patch.dict(
        "os.environ",
        {
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://example.test/v1",
            "LLM_MODEL": "test-model",
        },
        clear=False,
    )
    def test_draft_generation_preserves_raw_dsl_and_material_context(self):
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
                    '{"theme":"space","assetSlots":[{"slot":"hero","query":"rocket","subjects":["rocket"],"roles":["hero"]}]}'
                ),
                FakeResponse(
                    '{"layers":[{"id":"rocket","type":"asset","assetId":"doodle-034","src":"https://untrusted.example/rocket.svg"}]}'
                ),
            ]
        )

        result = generate_lockscreen_draft(
            "rocket lockscreen",
            requester=lambda *args, **kwargs: next(responses),
        )

        self.assertEqual(
            result["dsl"]["layers"][0]["src"],
            "https://untrusted.example/rocket.svg",
        )
        self.assertIn("doodle-034", result["context"]["allowedAssetIds"])
        self.assertEqual(
            result["context"]["materialCandidateGroups"][0]["slot"],
            "hero",
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
    def test_draft_context_keeps_material_slots_with_no_candidates(self):
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
                    '{"theme":"fantasy","assetSlots":[{"slot":"hero","query":"crystal dragon","subjects":["crystal-dragon"],"roles":["hero"]}]}'
                ),
                FakeResponse(
                    '{"layers":[{"id":"title","type":"text","content":"Dragon","x":195,"y":180}]}'
                ),
            ]
        )

        result = generate_lockscreen_draft(
            "crystal dragon lockscreen",
            requester=lambda *args, **kwargs: next(responses),
        )

        groups = result["context"]["materialCandidateGroups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["candidates"], [])

    @patch.dict(
        "os.environ",
        {
            "LLM_API_KEY": "test-key",
            "LLM_BASE_URL": "https://example.test/v1",
            "LLM_MODEL": "test-model",
        },
        clear=False,
    )
    def test_generation_can_select_a_trusted_frame_sequence(self):
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
                    '{"theme":"night","assetSlots":[{"slot":"decoration","query":"twinkling glowing star","subjects":["star"],"themes":["night"],"roles":["decoration"],"preferredPosition":"top-right"}]}'
                ),
                FakeResponse(
                    '{"layers":[{"id":"twinkle","type":"frameAnimation","assetId":"frame-star-twinkle-001","frames":["https://untrusted.example/01.png"],"fps":60,"x":280,"y":300,"width":86,"height":86}]}'
                ),
            ]
        )

        result = generate_lockscreen_dsl(
            "night lockscreen with a twinkling glowing star",
            requester=lambda *args, **kwargs: next(responses),
        )

        layer = result["layers"][0]
        self.assertEqual(layer["type"], "frameAnimation")
        self.assertEqual(layer["assetId"], "frame-star-twinkle-001")
        self.assertEqual(layer["fps"], 6)
        self.assertEqual(result["mode"], "dynamic")


if __name__ == "__main__":
    unittest.main()
