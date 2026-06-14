from utils.animation_defaults import normalize_animation_requirements


def test_prompt_animation_requirements_are_merged_with_model_output():
    requirements = normalize_animation_requirements(
        [
            {
                "target": "heart",
                "motion": "pulse",
                "complexity": "simple",
            }
        ],
        "爱心快速跳动，左上角的云朵缓慢向右飘动",
    )

    by_target = {requirement["target"]: requirement for requirement in requirements}
    assert by_target["heart"]["motion"] == "pulse"
    assert by_target["cloud"]["motion"] == "drift-right"
