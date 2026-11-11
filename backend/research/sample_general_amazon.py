"""Download bounded file-order review prefixes from the official Amazon Reviews'23 links.

This is an exploratory convenience sample, not a random sample of Amazon reviews.
Run before analyse_general_amazon.py. No dataset-provided Python code is executed.
"""
import hashlib
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
FOLDER = ROOT / "data/amazon-reviews-2023-sample"
COUNT_PER_CATEGORY = 20_000
CATEGORIES = ["Electronics", "Cell_Phones_and_Accessories"]
CARD_URL = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/raw/main/README.md"


def main():
    FOLDER.mkdir(parents=True, exist_ok=True)
    response = requests.get(CARD_URL, timeout=45)
    response.raise_for_status()
    card = response.text
    (FOLDER / "source_dataset_card.md").write_text(card, encoding="utf-8")
    listing_response = requests.get("https://huggingface.co/api/datasets/McAuley-Lab/Amazon-Reviews-2023/tree/main/raw/review_categories", params={"limit":100}, timeout=45)
    listing_response.raise_for_status()
    available = {entry["path"] for entry in listing_response.json()}
    info = requests.get("https://huggingface.co/api/datasets/McAuley-Lab/Amazon-Reviews-2023", timeout=45)
    info.raise_for_status()
    revision = info.json()["sha"]
    manifest = {"access_date": "2026-10-31", "source_card": CARD_URL,
                "source_revision": revision,
                "download_note": "Dataset-card datarepo compressed download returned 404; used the same publisher's Hugging Face raw files instead.",
                "sample_method": "first 20000 records in each selected review category file, in file order; not random",
                "categories": []}
    for category in CATEGORIES:
        source_path = "raw/review_categories/" + category + ".jsonl"
        if source_path not in available:
            raise RuntimeError(f"No official review file found for {category}")
        url = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/" + revision + "/" + source_path
        target = FOLDER / (category + "_first20000.jsonl")
        count = 0
        if target.exists():
            with target.open("rb") as source:
                count = sum(1 for _ in source)
        if count != COUNT_PER_CATEGORY:
            print(f"Streaming {category}: {url}", flush=True)
            count = 0
            temp = target.with_suffix(".partial")
            with requests.get(url, stream=True, timeout=(30, 90)) as download:
                download.raise_for_status()
                with temp.open("wb") as out:
                    for line in download.iter_lines(chunk_size=65536):
                        if not line.strip():
                            continue
                        json.loads(line)  # Ensure we persist complete valid records only.
                        out.write(line.rstrip(b"\n") + b"\n")
                        count += 1
                        if count == COUNT_PER_CATEGORY:
                            break
            if count != COUNT_PER_CATEGORY:
                raise RuntimeError(f"Only {count} records obtained from {category}")
            temp.replace(target)
        manifest["categories"].append({"category": category, "source_url": url,
            "records": count, "path": target.name, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
        print(f"{category}: {count} review records", flush=True)
    (FOLDER / "sample_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
