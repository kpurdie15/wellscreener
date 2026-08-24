import os
import requests
import pandas as pd

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

TARGET_COLS = ['State', 'Permit_ID', 'Well_Number', 'Operator', 'County', 'Type', 'Status']

def get_first_valid_col(df, possible_names, default="Unknown"):
    for col in possible_names:
        if col in df.columns:
            return df[col].astype(str)
    return pd.Series([default] * len(df))

def fetch_arcgis_full(url, max_records=50000, batch_size=2000):
    all_records = []
    offset = 0
    while offset < max_records:
        params = {
            'where': '1=1',
            'outFields': '*',
            'resultOffset': offset,
            'resultRecordCount': batch_size,
            'returnGeometry': 'false',
            'f': 'json'
        }
        try:
            res = requests.get(url, params=params, headers=HEADERS, timeout=30).json()
            features = res.get('features', [])
            if not features:
                break
            all_records.extend([f['attributes'] for f in features])
            if len(features) < batch_size:
                break
            offset += batch_size
        except Exception as e:
            print(f"Error fetching batch at offset {offset}: {e}")
            break
    return pd.DataFrame(all_records)

def scrape_ohio():
    print("Scraping Ohio...")
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Oil_and_Gas_Wells_Locations_of_Ohio/FeatureServer/0/query"
    df = fetch_arcgis_full(url, max_records=50000)
    if df.empty: return pd.DataFrame(columns=TARGET_COLS)
    clean_df = pd.DataFrame()
    clean_df['State'] = ['OH'] * len(df)
    clean_df['Permit_ID'] = get_first_valid_col(df, ['PERMIT_NBR', 'API_NUMBER', 'PERMIT'])
    clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NUMBER', 'WELL_NUM'])
    clean_df['Operator'] = get_first_valid_col(df, ['OWNER_NAME', 'OPERATOR'])
    clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
    clean_df['Type'] = get_first_valid_col(df, ['WELL_TYPE'])
    clean_df['Status'] = get_first_valid_col(df, ['WELL_STATUS'])
    return clean_df

def scrape_pa():
    print("Scraping Pennsylvania...")
    url = "https://gis.dep.pa.gov/depgisprd/rest/services/OilGas/OilGasAllStrayGas/MapServer/3/query"
    df = fetch_arcgis_full(url, max_records=50000)
    if df.empty: return pd.DataFrame(columns=TARGET_COLS)
    clean_df = pd.DataFrame()
    clean_df['State'] = ['PA'] * len(df)
    clean_df['Permit_ID'] = get_first_valid_col(df, ['PERMIT_NUMBER', 'AUTH_ID'])
    clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NUMBER'])
    clean_df['Operator'] = get_first_valid_col(df, ['OPERATOR_NAME'])
    clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
    clean_df['Type'] = get_first_valid_col(df, ['WELL_TYPE'])
    clean_df['Status'] = get_first_valid_col(df, ['WELL_STATUS'])
    return clean_df

def scrape_ny():
    print("Scraping New York...")
    url = "https://data.ny.gov/resource/3ub5-233v.json?$limit=50000"
    try:
        res = requests.get(url, headers=HEADERS, timeout=30).json()
        df = pd.DataFrame(res)
        if df.empty: return pd.DataFrame(columns=TARGET_COLS)
        clean_df = pd.DataFrame()
        clean_df['State'] = ['NY'] * len(df)
        clean_df['Permit_ID'] = get_first_valid_col(df, ['api_well_number'])
        clean_df['Well_Number'] = get_first_valid_col(df, ['well_name'])
        clean_df['Operator'] = get_first_valid_col(df, ['operator_name'])
        clean_df['County'] = get_first_valid_col(df, ['county'])
        clean_df['Type'] = get_first_valid_col(df, ['well_type'])
        clean_df['Status'] = get_first_valid_col(df, ['well_status'])
        return clean_df
    except Exception:
        return pd.DataFrame(columns=TARGET_COLS)

def scrape_wv():
    print("Scraping West Virginia...")
    url = "https://services.arcgis.com/jDGuO8tYggdCCnUJ/arcgis/rest/services/W_Virginia_1112018/FeatureServer/1/query"
    df = fetch_arcgis_full(url, max_records=50000)
    if df.empty: return pd.DataFrame(columns=TARGET_COLS)
    clean_df = pd.DataFrame()
    clean_df['State'] = ['WV'] * len(df)
    clean_df['Permit_ID'] = get_first_valid_col(df, ['API'])
    clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NO'])
    clean_df['Operator'] = get_first_valid_col(df, ['OPERATOR'])
    clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
    clean_df['Type'] = pd.Series(['Oil/Gas'] * len(df))
    clean_df['Status'] = get_first_valid_col(df, ['STATUS'])
    return clean_df

def scrape_ky():
    print("Scraping Kentucky...")
    url = "https://kgs.uky.edu/arcgis/rest/services/OilGas/KY_OilGas_Wells/MapServer/0/query"
    params = {
        'geometry': '-89.6,36.4,-81.9,39.1',
        'geometryType': 'esriGeometryEnvelope',
        'spatialRel': 'esriSpatialRelIntersects',
        'where': '1=1',
        'outFields': '*',
        'resultRecordCount': 10000,
        'f': 'json'
    }
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=30).json()
        features = res.get('features', [])
        df = pd.DataFrame([f['attributes'] for f in features])
        if df.empty: return pd.DataFrame(columns=TARGET_COLS)
        clean_df = pd.DataFrame()
        clean_df['State'] = ['KY'] * len(df)
        clean_df['Permit_ID'] = get_first_valid_col(df, ['PERMIT_NO'])
        clean_df['Well_Number'] = get_first_valid_col(df, ['WELL_NO'])
        clean_df['Operator'] = get_first_valid_col(df, ['OPERATOR_NAME', 'OPERATOR'])
        clean_df['County'] = get_first_valid_col(df, ['COUNTY'])
        clean_df['Type'] = get_first_valid_col(df, ['WELL_TYPE'])
        clean_df['Status'] = get_first_valid_col(df, ['STATUS'])
        return clean_df
    except Exception:
        return pd.DataFrame(columns=TARGET_COLS)

if __name__ == "__main__":
    dfs = [scrape_ohio(), scrape_pa(), scrape_ny(), scrape_wv(), scrape_ky()]
    full_df = pd.concat([d for d in dfs if not d.empty], ignore_index=True)
    full_df = full_df.fillna("Unknown")
    
    # Save output as compressed parquet
    full_df.to_parquet("wells_data.parquet", index=False)
    print(f"Dataset successfully compiled! Total Records: {len(full_df):,}")
