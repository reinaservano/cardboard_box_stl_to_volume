import unittest
from pathlib import Path

from stl_to_volume import build_parser


class ParserTests(unittest.TestCase):
    def test_accepts_box_stl_input_and_convex_hull(self) -> None:
        args = build_parser().parse_args(
            ["box.stl", "--pitch", "5", "--closure", "convex-hull", "--stl-units", "mm"]
        )

        self.assertEqual(args.input, Path("box.stl"))
        self.assertEqual(args.closure, "convex-hull")
        self.assertEqual(args.pitch, 5)
        self.assertEqual(args.stl_units, "mm")


if __name__ == "__main__":
    unittest.main()
