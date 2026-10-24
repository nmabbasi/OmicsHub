from __future__ import annotations

import hashlib
from http.client import HTTPMessage
import importlib.util
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "files/visium-example/prepare_inputs.py"
SPEC = importlib.util.spec_from_file_location("visium_download_fallback_under_test", SCRIPT)
visium = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(visium)


class FakeResponse:
    def __init__(self, body: bytes, *, status: int = 206, content_range: str = "bytes 0-3/4"):
        self.body = body
        self.offset = 0
        self.status = status
        self.headers = {"Content-Range": content_range, "Content-Length": str(len(body))}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size=-1):
        if size < 0:
            size = len(self.body) - self.offset
        result = self.body[self.offset:self.offset + size]
        self.offset += len(result)
        return result


def forbidden(url: str) -> HTTPError:
    return HTTPError(url, 403, "Forbidden", HTTPMessage(), None)


class VisiumDownloadFallbackTests(unittest.TestCase):
    def test_403_falls_back_to_exact_validated_206_range(self):
        payload = b"data"
        url = "https://example.test/mock.bin"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "mock.bin"
            with patch.object(visium, "SOURCE_SIZES", {"mock.bin": len(payload)}), patch.object(
                visium, "urlopen", side_effect=[forbidden(url), FakeResponse(payload)]
            ) as open_url:
                visium.download_file(url, target)
            self.assertEqual(target.read_bytes(), payload)
            request = open_url.call_args_list[1].args[0]
            self.assertEqual(request.get_header("Range"), "bytes=0-3")
            self.assertEqual(request.get_header("Accept-encoding"), "identity")
            self.assertEqual(request.get_header("User-agent"), "Mozilla/5.0")

    def test_two_segments_are_validated_and_appended_in_order(self):
        url = "https://example.test/mock.bin"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "mock.bin"
            with patch.object(visium, "SOURCE_SIZES", {"mock.bin": 8}), patch.object(
                visium, "RANGE_CHUNK_BYTES", 4
            ), patch.object(visium, "urlopen", side_effect=[
                forbidden(url),
                FakeResponse(b"abcd", content_range="bytes 0-3/8"),
                FakeResponse(b"efgh", content_range="bytes 4-7/8"),
            ]) as open_url:
                visium.download_file(url, target)
            self.assertEqual(target.read_bytes(), b"abcdefgh")
            self.assertEqual(open_url.call_args_list[2].args[0].get_header("Range"), "bytes=4-7")

    def test_concurrent_file_is_preserved_when_full_request_is_forbidden(self):
        url = "https://example.test/mock.bin"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "mock.bin"

            def full_request(_url, **_kwargs):
                target.write_bytes(b"concurrent file must survive")
                raise forbidden(url)

            with patch.object(visium, "SOURCE_SIZES", {"mock.bin": 4}), patch.object(
                visium, "urlopen", side_effect=full_request
            ) as open_url:
                with self.assertRaises(FileExistsError):
                    visium.download_file(url, target)
            self.assertEqual(open_url.call_count, 1)
            self.assertEqual(target.read_bytes(), b"concurrent file must survive")

    def test_non_206_range_and_short_body_fail_without_output(self):
        url = "https://example.test/mock.bin"
        short = FakeResponse(b"dat")
        short.headers["Content-Length"] = "4"
        responses = (FakeResponse(b"data", status=200), short)
        for response in responses:
            with self.subTest(status=response.status, body=response.body), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "mock.bin"
                with patch.object(visium, "SOURCE_SIZES", {"mock.bin": 4}), patch.object(
                    visium, "urlopen", side_effect=[forbidden(url), response]
                ):
                    with self.assertRaises(ValueError):
                        visium.download_file(url, target)
                self.assertFalse(target.exists())

    def test_malformed_content_range_fails_closed_and_removes_partial(self):
        url = "https://example.test/mock.bin"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "mock.bin"
            with patch.object(visium, "SOURCE_SIZES", {"mock.bin": 4}), patch.object(
                visium, "urlopen", side_effect=[forbidden(url), FakeResponse(b"data", content_range="bytes 1-4/5")]
            ):
                with self.assertRaisesRegex(ValueError, "Invalid ranged response"):
                    visium.download_file(url, target)
            self.assertFalse(target.exists())

    def test_source_over_budget_is_rejected_before_network_and_without_output(self):
        url = "https://example.test/mock.bin"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "mock.bin"
            with patch.object(visium, "SOURCE_SIZES", {"mock.bin": 5}), patch.object(
                visium, "MAX_BYTES", 4
            ), patch.object(visium, "urlopen") as open_url:
                with self.assertRaisesRegex(ValueError, "200 MiB limit"):
                    visium.download_file(url, target)
            open_url.assert_not_called()
            self.assertFalse(target.exists())

    def test_changed_checksum_aborts_staging_and_leaves_no_destination(self):
        payload = b"not-the-published-dataset"
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "prepared"

            def fetcher(_url: str, target: Path):
                target.write_bytes(payload)

            with patch.object(visium, "SOURCES", (("mock.h5", "0" * 64),)):
                with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
                    visium.prepare(destination, fetcher=fetcher)
            self.assertFalse(destination.exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])
            self.assertNotEqual(hashlib.sha256(payload).hexdigest(), "0" * 64)

    def test_existing_destination_is_not_clobbered_or_requested(self):
        url = "https://example.test/mock.bin"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "mock.bin"
            target.write_bytes(b"keep me")
            with patch.object(visium, "SOURCE_SIZES", {"mock.bin": 4}), patch.object(
                visium, "urlopen"
            ) as open_url:
                with self.assertRaises(FileExistsError):
                    visium.download_file(url, target)
            open_url.assert_not_called()
            self.assertEqual(target.read_bytes(), b"keep me")

    def test_prepare_refuses_existing_output_directory_without_fetching(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "prepared"
            target.mkdir()
            sentinel = target / "user-data.txt"
            sentinel.write_text("preserve", encoding="utf-8")

            def forbidden_fetcher(_url: str, _path: Path):
                self.fail("existing output must be rejected before downloads")

            with self.assertRaises(FileExistsError):
                visium.prepare(target, fetcher=forbidden_fetcher)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

    def test_transient_full_get_error_also_uses_ranged_fallback(self):
        payload = b"data"
        url = "https://example.test/mock.bin"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "mock.bin"
            with patch.object(visium, "SOURCE_SIZES", {"mock.bin": 4}), patch.object(
                visium, "urlopen", side_effect=[TimeoutError("network timeout"), FakeResponse(payload)]
            ):
                visium.download_file(url, target)
            self.assertEqual(target.read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
