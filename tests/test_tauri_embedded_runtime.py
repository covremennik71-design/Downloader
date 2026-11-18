import contextlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest


class EmbeddedTauriDownloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path("app/src-tauri/src/main.rs").read_text(encoding="utf-8")
        scripts = re.findall(r'let python_script = r#"(.*?)"#;', source, flags=re.DOTALL)
        if len(scripts) != 2:
            raise AssertionError("Expected metadata and download Python scripts")
        cls.download_script = scripts[1]

    def _load_script(self, fake_yt_dlp):
        previous = sys.modules.get("yt_dlp")
        sys.modules["yt_dlp"] = fake_yt_dlp
        namespace = {"__name__": "embedded_download_test"}
        try:
            exec(compile(self.download_script, "<embedded-download>", "exec"), namespace)
        finally:
            if previous is None:
                sys.modules.pop("yt_dlp", None)
            else:
                sys.modules["yt_dlp"] = previous
        return namespace

    def test_mp3_requires_ffmpeg_and_returns_structured_error(self):
        namespace = self._load_script(types.SimpleNamespace())
        namespace["find_ffmpeg"] = lambda _arg=None: None
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(output):
            result = namespace["download"](
                "https://youtu.be/abcdefghijk", "audio", "audio", folder
            )
        payload = json.loads(output.getvalue().strip())
        self.assertEqual(result, 1)
        self.assertEqual(payload["type"], "error")
        self.assertIn("FFmpeg", payload["error"])

    def test_missing_final_output_is_not_reported_as_success(self):
        class FakeYDL:
            def __init__(self, _options):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def extract_info(self, _url, download=False):
                return {"title": "sample", "ext": "webm"}

            def prepare_filename(self, _info):
                return str(Path(folder) / "sample.webm")

        namespace = self._load_script(types.SimpleNamespace(YoutubeDL=FakeYDL))
        namespace["find_ffmpeg"] = lambda _arg=None: None
        output = io.StringIO()
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(output):
            result = namespace["download"](
                "https://youtu.be/abcdefghijk", "360p", "video", folder
            )
        payload = json.loads(output.getvalue().strip())
        self.assertEqual(result, 1)
        self.assertEqual(payload["type"], "error")
        self.assertIn("output file was not found", payload["error"])

    def test_existing_final_output_is_reported_with_its_real_path(self):
        with tempfile.TemporaryDirectory() as folder:
            output_path = Path(folder) / "sample.webm"
            output_path.write_bytes(b"video")

            class FakeYDL:
                def __init__(self, _options):
                    pass

                def __enter__(self):
                    return self

                def __exit__(self, *_args):
                    return False

                def extract_info(self, _url, download=False):
                    return {"title": "sample", "ext": "webm", "filepath": str(output_path)}

                def prepare_filename(self, _info):
                    return str(Path(folder) / "sample.webm")

            namespace = self._load_script(types.SimpleNamespace(YoutubeDL=FakeYDL))
            namespace["find_ffmpeg"] = lambda _arg=None: None
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = namespace["download"](
                    "https://youtu.be/abcdefghijk", "360p", "video", folder
                )
            payload = json.loads(output.getvalue().strip())
            self.assertEqual(result, 0)
            self.assertEqual(payload["type"], "complete")
            self.assertEqual(payload["filename"], str(output_path))


if __name__ == "__main__":
    unittest.main()
