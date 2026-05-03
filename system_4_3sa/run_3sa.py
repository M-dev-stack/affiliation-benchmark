#!/usr/bin/env python3
"""
3SA baseline runner.
Replicates 3SA approach (Munoz-Jordan et al. 2025) using the ROR v2
affiliation matching endpoint with edit-distance based matching.
"""

import csv
import requests
import time
import sys
from tqdm import tqdm

INPUT_CSV  = "testset.csv"
OUTPUT_CSV = "system_4_3sa/3sa_results.csv"
ROR_API    = "https://api.ror.org/v2/organizations"

def query_ror(aff_str, retries=3):
    params = {"affiliation": aff_str}
    for attempt in range(retries):
        try:
            resp = requests.get(ROR_API, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                ror_ids = []
                for item in data.get("items", []):
                    if item.get("chosen", False):
                        ror_id = item["organization"]["id"].replace("https://ror.org/", "")
                        ror_ids.append(ror_id)
                return ror_ids
            elif resp.status_code == 429:
                print(f"\nRate limited. Waiting {5 * (attempt+1)}s...")
                time.sleep(5 * (attempt + 1))
        except requests.exceptions.RequestException as e:
            print(f"\nRequest error: {e}. Retrying...")
            time.sleep(3 * (attempt + 1))
    return []

def main():
    rows = []
    with open(INPUT_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    print(f"Loaded {len(rows)} affiliation strings from {INPUT_CSV}")
    print(f"Writing results to {OUTPUT_CSV}")

    written  = 0
    no_match = 0

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["an", "ror_id"])

        for row in tqdm(rows, desc="3SA progress"):
            an      = row["an"].strip()
            aff_str = row["aff_str"].strip()

            ror_ids = query_ror(aff_str)
            time.sleep(0.15)

            if ror_ids:
                for ror_id in ror_ids:
                    writer.writerow([an, ror_id])
                    written += 1
            else:
                writer.writerow([an, ""])
                no_match += 1

    print(f"\nDone. {written} ROR IDs written. {no_match} strings with no match.")
    print(f"Results saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
