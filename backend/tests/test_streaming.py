import json
from unittest.mock import patch

from llm_client import _stream_request_model_json
from orchestrator import stream_lockscreen_with_agent_loop


class FakeStreamingResponse:
    def __init__(self, chunks):
        self.chunks = chunks
        self.status_code = 200

    def raise_for_status(self):
        return None

    def iter_lines(self, decode_unicode=False):
        assert decode_unicode is True
        return iter(self.chunks)


def _data(payload):
    return f"data: {json.dumps(payload, ensure_ascii=False)}"


def test_stream_request_collects_reasoning_until_model_finish():
    calls = []
    response = FakeStreamingResponse(
        [
            _data(
                {
                    "choices": [
                        {
                            "delta": {"reasoning_content": "先分析主题。"},
                            "finish_reason": None,
                        }
                    ]
                }
            ),
            _data(
                {
                    "choices": [
                        {
                            "delta": {"content": '{"theme":"night"'},
                            "finish_reason": None,
                        }
                    ]
                }
            ),
            _data(
                {
                    "choices": [
                        {
                            "delta": {"content": ',"assetSlots":[]}'},
                            "finish_reason": "stop",
                        }
                    ]
                }
            ),
            "data: [DONE]",
        ]
    )

    def requester(*args, **kwargs):
        calls.append(kwargs)
        return response

    events = list(
        _stream_request_model_json(
            requester=requester,
            url="https://example.test/chat/completions",
            headers={},
            model="test-model",
            system_prompt="system",
            user_content="user",
            temperature=0.2,
            phase="intent",
        )
    )

    assert calls[0]["json"]["stream"] is True
    assert calls[0]["json"]["enable_thinking"] is True
    assert calls[0]["timeout"] == (10, 300)
    assert any(event["type"] == "thinking" and "分析主题" in event["delta"] for event in events)
    result = next(event["data"] for event in events if event["type"] == "model_result")
    assert result == {"theme": "night", "assetSlots": []}


def test_stream_request_rejects_connection_closed_without_finish_reason():
    response = FakeStreamingResponse(
        [
            _data(
                {
                    "choices": [
                        {
                            "delta": {"content": '{"theme":"night"}'},
                            "finish_reason": None,
                        }
                    ]
                }
            )
        ]
    )

    try:
        list(
            _stream_request_model_json(
                requester=lambda *args, **kwargs: response,
                url="https://example.test/chat/completions",
                headers={},
                model="test-model",
                system_prompt="system",
                user_content="user",
                temperature=0.2,
                phase="intent",
            )
        )
    except RuntimeError as error:
        assert "finish_reason" in str(error)
    else:
        raise AssertionError("stream should require a model completion signal")


@patch("orchestrator.generate_lockscreen_draft_stream")
def test_stream_orchestrator_emits_final_dsl(mock_draft_stream):
    mock_draft_stream.return_value = iter(
        [
            {"type": "phase", "phase": "intent", "status": "running", "label": "理解需求"},
            {
                "type": "draft_result",
                "dsl": {
                    "version": "1.0",
                    "canvas": {"width": 390, "height": 844},
                    "theme": "night",
                    "background": {"type": "color", "value": "#020617"},
                    "layers": [],
                },
                "context": {},
            },
        ]
    )

    events = list(stream_lockscreen_with_agent_loop("night lockscreen"))

    assert events[0]["type"] == "phase"
    final = events[-1]
    assert final["type"] == "final"
    assert final["dsl"]["canvas"] == {"width": 390, "height": 844}
    assert final["dsl"]["_debug"]["usedFallback"] is False


def test_stream_orchestrator_emits_fallback_draw_before_final():
    def draft_stream(prompt):
        yield {
            "type": "draft_result",
            "dsl": {
                "version": "1.0",
                "canvas": {"width": 390, "height": 844},
                "theme": "night",
                "background": {"type": "color", "value": "#020617"},
                "layers": [],
            },
            "context": {
                "materialCandidateGroups": [
                    {
                        "slot": "decoration",
                        "requirement": {
                            "subjects": ["moon"],
                            "query": "moon",
                        },
                        "candidates": [],
                    }
                ]
            },
        }

    events = list(
        stream_lockscreen_with_agent_loop(
            "moon in the top-left",
            draft_stream_factory=draft_stream,
        )
    )

    fallback_event = next(
        event for event in events if event["type"] == "fallback_draw"
    )
    final = events[-1]
    assert fallback_event["targets"] == ["moon"]
    assert final["type"] == "final"
    assert any(
        layer.get("shape") == "crescent"
        for layer in final["dsl"]["layers"]
    )


def test_stream_orchestrator_emits_animation_fallback_event():
    def draft_stream(prompt):
        yield {
            "type": "draft_result",
            "dsl": {
                "version": "1.0",
                "canvas": {"width": 390, "height": 844},
                "theme": "sky",
                "background": {"type": "color", "value": "#38bdf8"},
                "layers": [],
            },
            "context": {
                "intent": {
                    "animationRequirements": [
                        {
                            "target": "cloud",
                            "motion": "drift-right",
                            "complexity": "simple",
                        }
                    ]
                }
            },
        }

    events = list(
        stream_lockscreen_with_agent_loop(
            "clouds drifting to the right",
            draft_stream_factory=draft_stream,
        )
    )

    event = next(
        item for item in events if item["type"] == "animation_fallback"
    )
    assert event["animations"][0]["motion"] == "drift-right"


def test_stream_orchestrator_emits_complex_animation_notice():
    def draft_stream(prompt):
        yield {
            "type": "draft_result",
            "dsl": {
                "version": "1.0",
                "canvas": {"width": 390, "height": 844},
                "theme": "fantasy",
                "background": {"type": "color", "value": "#312e81"},
                "layers": [
                    {
                        "id": "title",
                        "type": "text",
                        "content": "Fantasy",
                        "x": 195,
                        "y": 180,
                    }
                ],
            },
            "context": {
                "intent": {
                    "animationRequirements": [
                        {
                            "target": "castle",
                            "motion": "transform-and-fly",
                            "complexity": "complex",
                        }
                    ]
                }
            },
        }

    events = list(
        stream_lockscreen_with_agent_loop(
            "castle transforms into a dragon",
            draft_stream_factory=draft_stream,
        )
    )

    event = next(
        item for item in events if item["type"] == "animation_unavailable"
    )
    assert event["notices"][0]["target"] == "castle"
    assert events[-1]["dsl"]["_debug"]["usedFallback"] is False


def test_stream_orchestrator_emits_interaction_ready_event():
    def draft_stream(prompt):
        yield {
            "type": "draft_result",
            "dsl": {
                "version": "1.0",
                "canvas": {"width": 390, "height": 844},
                "theme": "cute",
                "background": {"type": "color", "value": "#fb7185"},
                "layers": [
                    {
                        "id": "heart",
                        "type": "shape",
                        "shape": "heart",
                        "x": 290,
                        "y": 80,
                        "width": 52,
                        "height": 48,
                    }
                ],
            },
            "context": {
                "intent": {
                    "interactionRequirements": [
                        {
                            "target": "heart",
                            "trigger": {"type": "tap"},
                            "actions": [
                                {
                                    "type": "animate",
                                    "animation": "pulse",
                                }
                            ],
                        }
                    ]
                }
            },
        }

    events = list(
        stream_lockscreen_with_agent_loop(
            "点击爱心跳动",
            draft_stream_factory=draft_stream,
        )
    )

    ready = next(
        event for event in events if event["type"] == "interaction_ready"
    )
    assert ready["interactions"][0]["targetId"] == "heart"
    assert events[-1]["dsl"]["interactions"][0]["targetId"] == "heart"


def test_stream_emits_interaction_ready_for_model_supplied_interaction():
    def draft_stream(prompt):
        yield {
            "type": "draft_result",
            "dsl": {
                "version": "1.0",
                "canvas": {"width": 390, "height": 844},
                "theme": "cute",
                "background": {"type": "color", "value": "#fb7185"},
                "layers": [
                    {
                        "id": "heart",
                        "type": "shape",
                        "shape": "heart",
                        "x": 290,
                        "y": 80,
                        "width": 52,
                        "height": 48,
                    }
                ],
                "interactions": [
                    {
                        "id": "heart-tap",
                        "targetId": "heart",
                        "trigger": {"type": "tap"},
                        "actions": [
                            {
                                "type": "animate",
                                "animation": "pulse",
                            }
                        ],
                    }
                ],
            },
            "context": {"intent": {"interactionRequirements": []}},
        }

    events = list(
        stream_lockscreen_with_agent_loop(
            "点击爱心跳动",
            draft_stream_factory=draft_stream,
        )
    )

    ready = next(
        event for event in events if event["type"] == "interaction_ready"
    )
    assert ready["interactions"][0]["targetId"] == "heart"
    assert ready["interactions"][0]["trigger"] == "tap"


def test_stream_preserves_renderable_dsl_when_repair_errors_remain():
    def draft_stream(prompt):
        yield {
            "type": "draft_result",
            "dsl": {
                "version": "1.0",
                "canvas": {"width": 390, "height": 844},
                "theme": "night",
                "background": {"type": "color", "value": "#020617"},
                "layers": [
                    {
                        "id": "title",
                        "type": "text",
                        "content": "Keep streamed design",
                        "x": 195,
                        "y": 180,
                    }
                ],
            },
            "context": {"intent": {"interactionRequirements": []}},
        }

    events = list(
        stream_lockscreen_with_agent_loop(
            "night lockscreen with weather",
            draft_stream_factory=draft_stream,
            repairer=lambda prompt, dsl, errors, context: dsl,
        )
    )

    assert all(event["type"] != "error" for event in events)
    assert events[-1]["dsl"]["layers"][0]["content"] == "Keep streamed design"
    assert events[-1]["dsl"]["_debug"]["usedFallback"] is False
    assert events[-1]["dsl"]["_debug"]["errorsAfterRepair"]
