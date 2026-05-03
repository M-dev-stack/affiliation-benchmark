import pandas as pd
from tqdm import tqdm
from affilgood import AffilGood

# --- Config ---
INPUT_FILE  = "testset.csv"
OUTPUT_FILE = "system_5_affilgood/affilgood_results.csv"

# --- Load input ---
df = pd.read_csv(INPUT_FILE)
print(f"Loaded {len(df)} rows from {INPUT_FILE}")

# --- Init AffilGood ---
af = AffilGood(
    enable_entity_linking=True,
    linking_config={
        "reranker": None,
        "threshold": 0.5
    }
)

# --- Run and collect results ---
rows = []

for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing affiliations"):
    an      = row["an"]
    aff_str = str(row["aff_str"])

    try:
        result = af.process([aff_str])
        ror_ids = []

        for output in result[0].get("outputs", []):
            for inst in output.get("institutions", []):
                id_block = inst.get("id")
                if id_block and id_block.get("ror_id"):
                    raw = id_block["ror_id"]
                    ror_ids.append(raw.replace("https://ror.org/", ""))
            for sub in output.get("subunits", []):
                id_block = sub.get("id")
                if id_block and id_block.get("ror_id"):
                    raw = id_block["ror_id"]
                    ror_ids.append(raw.replace("https://ror.org/", ""))

    except Exception as e:
        print(f"Error on an={an}: {e}")
        ror_ids = []

    if ror_ids:
        for ror_id in ror_ids:
            rows.append({"an": an, "ror_id": ror_id})
    else:
        rows.append({"an": an, "ror_id": ""})

# --- Write output ---
out_df = pd.DataFrame(rows, columns=["an", "ror_id"])
out_df.to_csv(OUTPUT_FILE, index=False)
print(f"\nDone! {len(out_df)} rows written to {OUTPUT_FILE}")
