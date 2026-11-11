import io
import unittest
from contextlib import redirect_stdout

from knowledge_assistant.__main__ import main


class MainTests(unittest.TestCase):
    def test_main_prints_project_status(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            main()

        self.assertIn("Knowledge Assistant", output.getvalue())
        self.assertIn("load documents", output.getvalue())


if __name__ == "__main__":
    unittest.main()
