import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

RELEASE_ROOT = Path(__file__).resolve().parents[3]
if str(RELEASE_ROOT) not in sys.path:
    sys.path.insert(0, str(RELEASE_ROOT))

from tools.verify_release import verify_manifest


def write_manifest(root, *entries):
    manifest = root / "CHECKSUMS.sha256"
    manifest.write_text("\n".join(entries) + "\n", encoding="utf-8")
    return manifest


class ReleaseIntegrityTests(unittest.TestCase):
    def test_valid_files_verify_without_modification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "docs" / "example file.txt"
            payload.parent.mkdir()
            payload.write_bytes(b"Keep the original bytes.\n")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest = write_manifest(root, f"{digest}  docs/example file.txt")
            before = payload.read_bytes()

            code, report = verify_manifest(manifest)

            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "verified")
            self.assertEqual(report["checked_files"], 1)
            self.assertEqual(payload.read_bytes(), before)

    def test_missing_and_modified_files_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "changed.txt"
            payload.write_text("before", encoding="utf-8")
            original_hash = hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest = write_manifest(
                root,
                f"{original_hash}  changed.txt",
                f"{original_hash}  missing.txt",
            )
            payload.write_text("after", encoding="utf-8")

            code, report = verify_manifest(manifest)

            self.assertEqual(code, 1)
            self.assertEqual(report["status"], "integrity_failure")
            self.assertEqual(
                {item["status"] for item in report["mismatches"]},
                {"hash_mismatch", "missing_or_unresolvable"},
            )

    def test_unsafe_or_duplicate_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "safe.txt"
            payload.write_text("safe", encoding="utf-8")
            digest = hashlib.sha256(payload.read_bytes()).hexdigest()
            manifest = write_manifest(
                root,
                f"{digest}  safe.txt",
                f"{digest}  safe.txt",
                f"{digest}  ../outside.txt",
                f"{digest}  C:/outside.txt",
                f"{digest}  safe\\child.txt",
                f"{digest}  safe\x00child.txt",
            )

            code, report = verify_manifest(manifest)

            self.assertEqual(code, 2)
            self.assertEqual(report["status"], "invalid_manifest")
            self.assertEqual(len(report["errors"]), 5)

    def test_empty_manifest_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = write_manifest(Path(directory))
            code, report = verify_manifest(manifest)
            self.assertEqual(code, 2)
            self.assertEqual(report["errors"], ["manifest contains no file entries"])

    def test_unlisted_release_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            listed = root / "listed.txt"
            listed.write_text("listed", encoding="utf-8")
            (root / "forgotten.txt").write_text("forgotten", encoding="utf-8")
            digest = hashlib.sha256(listed.read_bytes()).hexdigest()
            manifest = write_manifest(root, f"{digest}  listed.txt")

            code, report = verify_manifest(manifest)

            self.assertEqual(code, 2)
            self.assertEqual(report["unlisted_files"], ["forgotten.txt"])

    def test_published_manifest_matches_this_release(self):
        manifest = RELEASE_ROOT / "CHECKSUMS.sha256"
        code, report = verify_manifest(manifest)
        self.assertEqual(code, 0, json.dumps(report, indent=2))


if __name__ == "__main__":
    unittest.main()
