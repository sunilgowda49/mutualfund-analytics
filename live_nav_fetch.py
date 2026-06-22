
import os
import time
import requests
import pandas as pd

RAW_DIR = "data/raw"

# All 5 required schemes from the task (+ Kotak)
SCHEMES = {
    "HDFC Top 100 Direct": 125497,
    "SBI Bluechip":        119551,
    "ICICI Bluechip":      120503,
    "Nippon Large Cap":    118632,
    "Axis Bluechip":       119092,
    "Kotak Bluechip":      120841,
}

BASE_URL = "https://api.mfapi.in/mf"


def fetch_nav(scheme_code: int, scheme_name: str) -> pd.DataFrame | None:
    url = f"{BASE_URL}/{scheme_code}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        meta = data.get("meta", {})
        records = data.get("data", [])

        if not records:
            print(f"  No NAV records returned for {scheme_name}")
            return None

        df = pd.DataFrame(records)
        df["scheme_code"] = scheme_code
        df["scheme_name"] = scheme_name
        df["fund_house"]  = meta.get("fund_house", "")
        df["scheme_type"] = meta.get("scheme_type", "")
        df["scheme_category"] = meta.get("scheme_category", "")

        # Normalise columns
        df.rename(columns={"date": "nav_date", "nav": "nav_value"}, inplace=True)
        df["nav_date"]  = pd.to_datetime(df["nav_date"],  dayfirst=True, errors="coerce")
        df["nav_value"] = pd.to_numeric(df["nav_value"], errors="coerce")
        df.sort_values("nav_date", inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    except requests.exceptions.ConnectionError:
        print(f"  Connection error for {scheme_name}. Check your internet connection.")
    except requests.exceptions.Timeout:
        print(f"  Request timed out for {scheme_name}.")
    except requests.exceptions.HTTPError as e:
        print(f"  HTTP error for {scheme_name}: {e}")
    except Exception as e:
        print(f"  Unexpected error for {scheme_name}: {e}")

    return None


def fetch_all_schemes():
    os.makedirs(RAW_DIR, exist_ok=True)
    all_frames = []

    print("Fetching live NAV data from mfapi.in ...\n")
    print("=" * 60)

    for name, code in SCHEMES.items():
        print(f"  Fetching: {name} (code: {code}) ...")
        df = fetch_nav(code, name)

        if df is not None:
            # Save individual file
            filepath = os.path.join(RAW_DIR, f"nav_{code}.csv")
            df.to_csv(filepath, index=False)
            print(f"    Saved {len(df)} rows → {filepath}")
            print(f"    Date range: {df['nav_date'].min().date()} to {df['nav_date'].max().date()}")
            print(f"    Latest NAV: ₹{df['nav_value'].iloc[-1]:.4f}")
            all_frames.append(df)
        else:
            print(f"    Skipped {name}.")

        time.sleep(0.5)  # Be polite to the API

    if all_frames:
        combined = pd.concat(all_frames, ignore_index=True)
        combined_path = os.path.join(RAW_DIR, "nav_all_schemes.csv")
        combined.to_csv(combined_path, index=False)
        print(f"\n Combined file saved → {combined_path}")
        print(f"  Total records: {len(combined)}")
        print(f"  Schemes fetched: {combined['scheme_name'].nunique()}")
    else:
        print("\n No data fetched. Check your internet connection and try again.")

    print("\n Live NAV fetch complete.")


if __name__ == "__main__":
    fetch_all_schemes()
