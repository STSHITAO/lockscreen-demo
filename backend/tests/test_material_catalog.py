import unittest

from material_catalog import get_asset, load_materials, search_materials


class MaterialCatalogTests(unittest.TestCase):
    def test_loads_every_tagged_static_and_animation_material(self):
        materials = load_materials()

        self.assertEqual(len(materials), 152)
        self.assertEqual(len({asset["assetId"] for asset in materials}), 152)

        animation = get_asset("frame-star-twinkle-001")
        self.assertEqual(animation["assetType"], "frameSequence")
        self.assertEqual(animation["frameCount"], 5)
        self.assertEqual(animation["fps"], 6)
        self.assertEqual(animation["poster"], animation["frames"][2])

    def test_searches_each_material_slot_independently(self):
        rockets = search_materials(
            {
                "query": "cute space rocket",
                "subjects": ["rocket"],
                "themes": ["space"],
                "roles": ["hero"],
            },
            limit=5,
        )
        ufos = search_materials(
            {
                "query": "alien ufo",
                "subjects": ["ufo"],
                "themes": ["space"],
            },
            limit=5,
        )

        self.assertEqual(rockets[0]["assetId"], "doodle-034")
        self.assertIn("doodle-093", [asset["assetId"] for asset in rockets])
        self.assertEqual([asset["assetId"] for asset in ufos], ["doodle-057"])

    def test_role_is_a_ranking_hint_not_a_hard_subject_filter(self):
        planets = search_materials(
            {
                "query": "small moon decoration",
                "subjects": ["planet"],
                "roles": ["decoration"],
                "themes": ["space"],
            },
            limit=5,
        )

        self.assertEqual(planets[0]["assetId"], "doodle-091")

    def test_get_asset_returns_only_catalog_entries(self):
        self.assertEqual(get_asset("doodle-057")["src"], "/materials/svg/doodle-57.svg")
        self.assertIsNone(get_asset("not-in-catalog"))

    def test_searches_frame_animation_by_chinese_tags(self):
        results = search_materials(
            {
                "query": "\u95ea\u70c1\u53d1\u5149\u661f\u661f",
                "subjects": ["star"],
                "themes": ["night"],
            },
            limit=5,
        )

        self.assertEqual(results[0]["assetId"], "frame-star-twinkle-001")
        self.assertEqual(results[0]["assetType"], "frameSequence")


if __name__ == "__main__":
    unittest.main()
