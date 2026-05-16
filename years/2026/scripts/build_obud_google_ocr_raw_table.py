from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = ROOT / "data" / "raw" / "obud_reviews" / "screenshots"
OCR_TEXT_DIR = ROOT / "data" / "raw" / "obud_reviews" / "ocr_text"
OUTPUT_PATH = ROOT / "data" / "interim" / "obud_reviews" / "google_vision_ocr_raw.csv"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def image_files() -> list[Path]:
    return sorted(
        [path for path in SCREENSHOTS_DIR.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES],
        key=lambda path: path.name,
    )


def main() -> None:
    rows: list[dict[str, object]] = []
    for order, image_path in enumerate(image_files(), start=1):
        text_path = OCR_TEXT_DIR / f"{image_path.stem}.google_vision.txt"
        text = text_path.read_text(encoding="utf-8") if text_path.exists() else ""
        rows.append(
            {
                "review_capture_order": order,
                "source_image": image_path.name,
                "ocr_engine": "google_vision_document_text_detection",
                "ocr_text_path": str(text_path.relative_to(ROOT)) if text_path.exists() else "",
                "ocr_text_chars": len(text),
                "ocr_text": text,
            }
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "review_capture_order",
                "source_image",
                "ocr_engine",
                "ocr_text_path",
                "ocr_text_chars",
                "ocr_text",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"created={OUTPUT_PATH}")
    print(f"rows={len(rows)}")
    print(f"missing_text_files={sum(1 for row in rows if not row['ocr_text_path'])}")
    print(f"total_chars={sum(int(row['ocr_text_chars']) for row in rows)}")


if __name__ == "__main__":
    main()
