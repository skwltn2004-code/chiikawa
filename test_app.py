import unittest
from io import BytesIO
from PIL import Image
from streamlit.testing.v1 import AppTest
from app import AXES, CHARACTERS, QUESTIONS, calculate, make_card, evidence, ROOT


class AppTests(unittest.TestCase):
    def test_scoring_bounds_and_validation(self):
        low = [next(i for i, o in enumerate(q["options"]) if o["score"] == 0) for q in QUESTIONS]
        high = [next(i for i, o in enumerate(q["options"]) if o["score"] == 3) for q in QUESTIONS]
        self.assertEqual(calculate(low)[0], [0] * len(AXES))
        self.assertEqual(calculate(high)[0], [100] * len(AXES))
        with self.assertRaises(ValueError):
            calculate([None] * len(QUESTIONS))
        vector, ranked, ties = calculate(high)
        self.assertEqual(len(evidence(high, ranked[0][1])), 3)
        data = make_card("테스트", ranked[0][1], vector, ties)
        self.assertEqual(Image.open(BytesIO(data)).size, (1080, 1900))

    def test_all_seven_characters_reachable_and_images(self):
        self.assertEqual(len(CHARACTERS), 7)
        self.assertEqual(len(QUESTIONS), 16)
        for c in CHARACTERS:
            answers = [min(range(4), key=lambda a: abs(q["options"][a]["score"] * 100 / 3 - c["vector"][q["axis"]])) for q in QUESTIONS]
            vector, ranked, ties = calculate(answers)
            self.assertEqual(ranked[0][1]["name"], c["name"])
            with Image.open(ROOT / "assets" / "characters" / c["image"]) as im:
                im.verify()
            self.assertEqual(Image.open(BytesIO(make_card("지수", c, vector, ties))).size, (1080, 1900))

    def test_full_journey_edit_and_reset(self):
        at = AppTest.from_file(str(ROOT / "app.py")).run()
        self.assertFalse(at.exception)
        at.button[0].click().run()
        self.assertTrue(at.button[1].disabled)
        at.radio[0].set_value(2).run()
        at.button[1].click().run()
        at.button[0].click().run()
        self.assertEqual(at.radio[0].value, 2)
        at.radio[0].set_value(1).run()
        at.button[1].click().run()
        for _ in range(len(QUESTIONS) - 1):
            at.radio[0].set_value(0).run()
            at.button[1].click().run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state["page"], "result")
        old = calculate(at.session_state["answers"])[0]
        next(b for b in at.button if b.label == "답변 수정하기").click().run()
        self.assertEqual(at.radio[0].value, 1)
        at.radio[0].set_value(3).run()
        for _ in range(len(QUESTIONS)):
            at.button[1].click().run()
        self.assertFalse(at.exception)
        self.assertNotEqual(old, calculate(at.session_state["answers"])[0])
        next(b for b in at.button if b.label == "다시 테스트하기").click().run()
        self.assertEqual(at.session_state["page"], "home")
        self.assertEqual(at.session_state["answers"], [None] * len(QUESTIONS))


if __name__ == "__main__":
    unittest.main()
