"""
Script to verify and inspect mock seed data for Indian Standards.
"""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    seed_file = root / "data" / "mock" / "standards_seed.json"
    if not seed_file.exists():
        print(f"[ERROR] Seed file not found at: {seed_file}")
        return

    with open(seed_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[OK] Successfully loaded {len(data)} Indian Standards from seed dataset.")
    for idx, item in enumerate(data, 1):
        print(f" {idx}. {item.get('standard_number')}: {item.get('title')[:60]}... ({item.get('demo_tag')})")

if __name__ == "__main__":
    main()
