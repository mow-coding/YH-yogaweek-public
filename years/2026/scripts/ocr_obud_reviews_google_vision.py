from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = ROOT / "data" / "raw" / "obud_reviews" / "screenshots"
OCR_TEXT_DIR = ROOT / "data" / "raw" / "obud_reviews" / "ocr_text"
MANIFEST_PATH = ROOT / "data" / "interim" / "obud_reviews" / "google_vision_ocr_manifest.csv"
PROJECT_API_KEY_FILE = ROOT / ".secrets" / "google-api.txt"
DOWNLOAD_API_KEY_FILES = [
    Path.home() / "Downloads" / "google-api.txt",
    Path.home() / "다운로드" / "google-api.txt",
]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Google Cloud Vision OCR for Obud review screenshots."
    )
    parser.add_argument(
        "--api-key-file",
        type=Path,
        default=None,
        help="Text file containing a Google API key. Defaults to .secrets/google-api.txt, GOOGLE_API_KEY_FILE, or Downloads/google-api.txt.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only the first N screenshots. Useful for testing.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run OCR even when an output text file already exists.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.15,
        help="Seconds to wait between API calls.",
    )
    return parser.parse_args()


def api_key_candidates(api_key_file: Path | None) -> list[Path]:
    if api_key_file is not None:
        return [api_key_file]

    env_file = os.environ.get("GOOGLE_API_KEY_FILE", "").strip()
    candidates = [PROJECT_API_KEY_FILE]
    if env_file:
        candidates.append(Path(env_file))
    candidates.extend(DOWNLOAD_API_KEY_FILES)
    return candidates


def read_api_key(api_key_file: Path | None) -> str:
    api_key_from_env = os.environ.get("GOOGLE_API_KEY", "").strip()
    if api_key_from_env:
        return api_key_from_env

    tried_paths: list[str] = []
    for candidate in api_key_candidates(api_key_file):
        tried_paths.append(str(candidate))
        if not candidate.exists():
            continue
        api_key = candidate.read_text(encoding="utf-8-sig").strip()
        if not api_key:
            raise ValueError(f"Google API key file is empty: {candidate}")
        return api_key

    raise FileNotFoundError(
        "Google API key file not found. "
        f"Tried: {', '.join(tried_paths)}. Set GOOGLE_API_KEY or GOOGLE_API_KEY_FILE."
    )


def image_files() -> list[Path]:
    return sorted(
        [path for path in SCREENSHOTS_DIR.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES],
        key=lambda path: path.name,
    )


def call_google_vision(api_key: str, image_path: Path) -> dict[str, Any]:
    image_content = base64.b64encode(image_path.read_bytes()).decode("ascii")
    payload = {
        "requests": [
            {
                "image": {"content": image_content},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
                "imageContext": {"languageHints": ["ko", "en"]},
            }
        ]
    }
    response = requests.post(
        f"https://vision.googleapis.com/v1/images:annotate?key={api_key}",
        json=payload,
        timeout=90,
    )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Google Vision returned non-JSON response: {response.text[:500]}") from exc

    if response.status_code != 200 or "error" in data:
        error = data.get("error", {})
        message = error.get("message", str(data))
        status = error.get("status", "")
        code = error.get("code", response.status_code)
        raise RuntimeError(f"Google Vision API error {code} {status}: {message}")

    item_response = data.get("responses", [{}])[0]
    if "error" in item_response:
        error = item_response["error"]
        raise RuntimeError(
            f"Google Vision item error {error.get('code', '')}: {error.get('message', '')}"
        )

    return data


def write_manifest(rows: list[dict[str, object]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "review_capture_order",
        "source_image",
        "status",
        "text_chars",
        "text_path",
        "json_path",
        "error_message",
    ]
    with MANIFEST_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    api_key = read_api_key(args.api_key_file)
    OCR_TEXT_DIR.mkdir(parents=True, exist_ok=True)

    images = image_files()
    if args.limit is not None:
        images = images[: args.limit]

    manifest_rows: list[dict[str, object]] = []

    for order, image_path in enumerate(images, start=1):
        text_path = OCR_TEXT_DIR / f"{image_path.stem}.google_vision.txt"
        json_path = OCR_TEXT_DIR / f"{image_path.stem}.google_vision.response.json"

        if text_path.exists() and json_path.exists() and not args.force:
            text_chars = len(text_path.read_text(encoding="utf-8"))
            manifest_rows.append(
                {
                    "review_capture_order": order,
                    "source_image": image_path.name,
                    "status": "skipped_exists",
                    "text_chars": text_chars,
                    "text_path": str(text_path.relative_to(ROOT)),
                    "json_path": str(json_path.relative_to(ROOT)),
                    "error_message": "",
                }
            )
            continue

        try:
            data = call_google_vision(api_key, image_path)
            text = data.get("responses", [{}])[0].get("fullTextAnnotation", {}).get("text", "")
            text_path.write_text(text, encoding="utf-8")
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            manifest_rows.append(
                {
                    "review_capture_order": order,
                    "source_image": image_path.name,
                    "status": "ok",
                    "text_chars": len(text),
                    "text_path": str(text_path.relative_to(ROOT)),
                    "json_path": str(json_path.relative_to(ROOT)),
                    "error_message": "",
                }
            )
            print(f"ok {order}: {image_path.name} chars={len(text)}")
        except Exception as exc:
            manifest_rows.append(
                {
                    "review_capture_order": order,
                    "source_image": image_path.name,
                    "status": "error",
                    "text_chars": 0,
                    "text_path": str(text_path.relative_to(ROOT)),
                    "json_path": str(json_path.relative_to(ROOT)),
                    "error_message": str(exc),
                }
            )
            print(f"error {order}: {image_path.name}: {exc}")

        write_manifest(manifest_rows)
        time.sleep(args.sleep)

    write_manifest(manifest_rows)
    print(f"manifest={MANIFEST_PATH}")


if __name__ == "__main__":
    main()
