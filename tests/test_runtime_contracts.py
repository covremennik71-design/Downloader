import ast
from pathlib import Path
import unittest


class RuntimeContractTests(unittest.TestCase):
    def test_tk_widgets_are_not_mutated_from_worker_methods(self):
        source = Path("downloader.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        app_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "DownloaderApp"
        )
        worker_names = {"_get_info_thread", "_get_info_and_show_quality_dialog"}
        for method in (n for n in app_class.body if isinstance(n, ast.FunctionDef) and n.name in worker_names):
            with self.subTest(method=method.name):
                for node in ast.walk(method):
                    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                        continue
                    receiver = node.func.value
                    if (
                        isinstance(receiver, ast.Attribute)
                        and isinstance(receiver.value, ast.Name)
                        and receiver.value.id == "self"
                        and receiver.attr.endswith("_combo")
                    ):
                        self.fail(f"Worker method {method.name} directly calls a Tk widget method")

    def test_tauri_cancel_kills_the_child_process(self):
        source = Path("app/src-tauri/src/main.rs").read_text(encoding="utf-8")
        self.assertIn("static ACTIVE_DOWNLOAD", source)
        self.assertIn("child.kill()", source)
        self.assertNotIn("В реальной реализации нужно убить Python процесс", source)

    def test_repository_has_no_developer_machine_download_path(self):
        for path in ("config.json", "app/src/main.js", "README.md"):
            with self.subTest(path=path):
                source = Path(path).read_text(encoding="utf-8")
                self.assertNotIn("C:\\\\Users\\\\Smixr", source)
                self.assertNotIn("C:\\Users\\Smixr", source)

    def test_windows_scripts_use_repository_relative_paths(self):
        build = Path("build.bat").read_text(encoding="utf-8")
        dev = Path("dev.bat").read_text(encoding="utf-8")
        ffmpeg = Path("download_ffmpeg.bat").read_text(encoding="utf-8")
        self.assertIn('cd /d "%~dp0"', build)
        self.assertIn('pushd "app\\src-tauri"', dev)
        self.assertNotIn("Python314", build)
        self.assertIn("Invoke-WebRequest", ffmpeg)


if __name__ == "__main__":
    unittest.main()
