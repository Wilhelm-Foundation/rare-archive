"""Filter combined training JSONL by disease category keywords.

Reads combined_train.jsonl, filters records matching keyword patterns for a
given category, and writes category-specific train/val splits.

Usage:
    # Filter IEM cases with default 90/10 split
    python scripts/filter_category.py \
        --input data/combined_train.jsonl \
        --category iem \
        --output-dir data

    # Custom validation ratio
    python scripts/filter_category.py \
        --input data/combined_train.jsonl \
        --category iem \
        --output-dir data \
        --val-ratio 0.2

Output files:
    data/{category}_train.jsonl  — training split
    data/{category}_val.jsonl    — validation split

Supported categories: iem (Inborn Errors of Metabolism).
Add new categories by extending the CATEGORIES dict.
"""

import argparse
import json
import random
from pathlib import Path

# Disease category keyword sets
CATEGORIES = {
    "iem": [
        "phenylketonuria", "pku", "galactosemia", "maple syrup urine",
        "homocystinuria", "tyrosinemia", "alcaptonuria", "alkaptonuria",
        "gaucher", "fabry", "niemann-pick", "tay-sachs", "pompe",
        "hunter syndrome", "hurler", "mucopolysaccharidosis", "mps",
        "glycogen storage", "organic acidemia", "methylmalonic",
        "propionic acidemia", "isovaleric", "glutaric aciduria",
        "urea cycle", "ornithine transcarbamylase", "citrullinemia",
        "argininosuccinic", "medium-chain acyl-coa", "mcad",
        "very long-chain", "vlcad", "carnitine", "fatty acid oxidation",
        "lysosomal storage", "peroxisomal", "zellweger", "adrenoleukodystrophy",
        "wilson disease", "hemochromatosis", "menkes", "biotinidase",
        "congenital disorder of glycosylation", "cdg",
        "mitochondrial", "melas", "merrf", "leigh syndrome",
        "inborn error", "metabolic disorder", "enzyme deficiency",
    ],
}


def matches_category(record: dict, keywords: list[str]) -> bool:
    """Check if any message content matches category keywords."""
    text = json.dumps(record.get("messages", [])).lower()
    return any(kw in text for kw in keywords)


def main():
    parser = argparse.ArgumentParser(description="Filter training data by disease category")
    parser.add_argument("--input", required=True, help="Path to combined_train.jsonl")
    parser.add_argument("--category", required=True, choices=list(CATEGORIES.keys()),
                        help="Disease category to filter")
    parser.add_argument("--output-dir", default="data", help="Output directory")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation split ratio")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for split")
    args = parser.parse_args()

    keywords = CATEGORIES[args.category]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Filter records
    matched = []
    total = 0
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            record = json.loads(line)
            if matches_category(record, keywords):
                matched.append(record)

    print(f"Matched {len(matched)}/{total} records for category '{args.category}'")

    if not matched:
        print("No matches found — check keywords or input data")
        return

    # Split into train/val
    random.seed(args.seed)
    random.shuffle(matched)
    val_size = max(1, int(len(matched) * args.val_ratio))
    val_records = matched[:val_size]
    train_records = matched[val_size:]

    # Write outputs
    train_path = output_dir / f"{args.category}_train.jsonl"
    val_path = output_dir / f"{args.category}_val.jsonl"

    for path, records in [(train_path, train_records), (val_path, val_records)]:
        with open(path, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"Wrote {len(records)} records to {path}")


if __name__ == "__main__":
    main()
