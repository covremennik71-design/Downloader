import ast
from pathlib import Path
import re
import unittest


class EmbeddedPythonScriptTests(unittest.TestCase):
    def test_rust_embedded_python_scripts_are_valid(self):
        source = Path("app/src-tauri/src/main.rs").read_text(encoding="utf-8")
        scripts = re.findall(r'let python_script = r#"(.*?)"#;', source, flags=re.DOTALL)
        self.assertEqual(len(scripts), 2, "Expected metadata and download Python scripts")
        for index, script in enumerate(scripts, start=1):
            with self.subTest(script=index):
                ast.parse(script)
                self.assertIn("def normalize_youtube_url", script)


if __name__ == "__main__":
    unittest.main()
