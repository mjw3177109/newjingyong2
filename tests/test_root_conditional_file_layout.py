"""Guard against accidental swapping of the root IF analyzer and its tests.

These checks are intentionally independent of importing either target module.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "tools" / "build_root_conditional_review_queue.py"
TESTS = ROOT / "tests" / "test_root_conditional_target_frame.py"


class RootConditionalFileLayoutTests(unittest.TestCase):
    def test_analyzer_exports_entrypoint_and_builder(self):
        tree = ast.parse(ANALYZER.read_text(encoding="utf-8"))
        functions = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.assertIn("build_queue", functions)
        self.assertIn("main", functions)

    def test_target_frame_test_file_contains_test_case(self):
        tree = ast.parse(TESTS.read_text(encoding="utf-8"))
        classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
        self.assertIn("TargetFrameSelectionTests", classes)
        self.assertNotIn("build_queue", {node.name for node in tree.body if isinstance(node, ast.FunctionDef)})


if __name__ == "__main__":
    unittest.main()
