
import os
import glob
import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

def load_all_csvs():
    csv_files = glob.glob(os.path.join(RAW_DIR, "*.csv"))

    if not csv_files:
        print(f"No CSV files found in '{RAW_DIR}/'. Please place your 10 CSV datasets there.")
        return {}

    datasets = {}
    print(f"Found {len(csv_files)} CSV file(s)\n")
    print("=" * 60)

    for filepath in csv_files:
        filename = os.path.basename(filepath)
        name = os.path.splitext(filename)[0]

        try:
            df = pd.read_csv(filepath)
            datasets[name] = df

            print(f"\n FILE: {filename}")
            print(f"  Shape     : {df.shape[0]} rows x {df.shape[1]} columns")
            print(f"  Columns   : {list(df.columns)}")
            print(f"\n  Data types:")
            print(df.dtypes.to_string(header=False))
            print(f"\n  First 3 rows:")
            print(df.head(3).to_string(index=False))

            # Anomaly checks
            null_counts = df.isnull().sum()
            nulls = null_counts[null_counts > 0]
            dup_count = df.duplicated().sum()

            print(f"\n  Anomaly check:")
            if nulls.empty:
                print("    No null values found.")
            else:
                print(f"    Null values:\n{nulls.to_string()}")
            if dup_count > 0:
                print(f"    Duplicate rows: {dup_count}")
            else:
                print("    No duplicate rows.")

            print("-" * 60)

        except Exception as e:
            print(f"  ERROR reading {filename}: {e}")

    return datasets


def validate_amfi_codes(datasets):
    """Check that every scheme code in fund_master exists in nav_history."""
    print("\n AMFI Code Validation")
    print("=" * 60)

    if "fund_master" not in datasets:
        print("  'fund_master.csv' not found. Skipping AMFI validation.")
        return

    if "nav_history" not in datasets:
        print("  'nav_history.csv' not found. Skipping AMFI validation.")
        return

    df_master = datasets["fund_master"]
    df_nav    = datasets["nav_history"]

    # Detect the scheme code column (flexible naming)
    master_col = next((c for c in df_master.columns if "scheme_code" in c.lower() or "amfi" in c.lower()), None)
    nav_col    = next((c for c in df_nav.columns    if "scheme_code" in c.lower() or "amfi" in c.lower()), None)

    if not master_col or not nav_col:
        print(f"  Could not find scheme_code column.")
        print(f"  fund_master columns : {list(df_master.columns)}")
        print(f"  nav_history columns : {list(df_nav.columns)}")
        return

    master_codes = set(df_master[master_col].dropna().astype(str))
    nav_codes    = set(df_nav[nav_col].dropna().astype(str))
    missing      = master_codes - nav_codes

    print(f"  Total schemes in fund_master : {len(master_codes)}")
    print(f"  Total schemes in nav_history : {len(nav_codes)}")
    print(f"  Missing from nav_history     : {len(missing)}")

    if missing:
        print(f"\n  Missing codes: {sorted(missing)}")
    else:
        print("  All fund_master codes are present in nav_history.")

    # Save quality summary
    summary = {
        "total_master_schemes": len(master_codes),
        "total_nav_schemes":    len(nav_codes),
        "missing_count":        len(missing),
        "missing_codes":        sorted(missing),
    }
    summary_df = pd.DataFrame([summary])
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    summary_df.to_csv(os.path.join(PROCESSED_DIR, "data_quality_summary.csv"), index=False)
    print(f"\n  Quality summary saved to '{PROCESSED_DIR}/data_quality_summary.csv'")


def explore_fund_master(datasets):
    """Print unique fund houses, categories, sub-categories, and risk grades."""
    if "fund_master" not in datasets:
        return

    df = datasets["fund_master"]
    print("\n FUND MASTER EXPLORATION")
    print("=" * 60)

    for col_hint, label in [
        ("fund_house",    "Fund houses"),
        ("category",      "Categories"),
        ("sub_category",  "Sub-categories"),
        ("risk",          "Risk grades"),
    ]:
        col = next((c for c in df.columns if col_hint in c.lower()), None)
        if col:
            print(f"\n  {label} ({col}):")
            print(df[col].value_counts().to_string())


if __name__ == "__main__":
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    datasets = load_all_csvs()
    explore_fund_master(datasets)
    validate_amfi_codes(datasets)

    print("\n Day 1 data ingestion complete.")
