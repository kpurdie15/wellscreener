import io
import requests
import pandas as pd

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Standard Output Schema
TARGET_COLS = ['State', 'Permit_ID', 'Well_Number', 'Operator', 'County', 'Type', 'Status', 'Status_Category']

def normalize_status(state, status_val):
    """Maps state-specific internal status codes to standard categories."""
    s = str(status_val).upper().strip()
    
    if state == 'NY':
        if any(k in s for k in ['PRODUCING', 'ACTIVE', 'DRILLING', 'ACTIVE PRODUCING']):
            return 'Active'
        elif any(k in s for k in ['PLUGGED', 'ABANDONED', 'PLUGGED AND ABANDONED', 'CANCELLED']):
            return 'Plugged / Abandoned'
        elif any(k in s for k in ['PERMIT', 'LOCATION', 'APPLICATION']):
            return 'Permitted / Undrilled'
            
    elif state == 'OH':
        if s in ['AC', 'PR', 'DR', 'ACTIVE', 'PRODUCING']:
            return 'Active'
        elif s in ['PA', 'PL', 'AB', 'CANCEL', 'PLUGGED', 'PLUGGED & ABANDONED']:
            return 'Plugged / Abandoned'
        elif s in ['AP', 'PM', 'PERMIT']:
            return 'Permitted / Undrilled'

    elif state == 'PA':
        if any(k in s for k in ['ACTIVE', 'OPERATING', 'DRILLING']):
            return 'Active'
        elif any(k in s for k in ['PLUGGED', 'ABANDONED', 'INACTIVE']):
            return 'Plugged / Abandoned'
        elif any(k in s for k in ['PERMITTED', 'APPROVED']):
            return 'Permitted / Undrilled'

    elif state == 'WV':
        if any(k in s for k in ['PRODUCING', 'ACTIVE', 'OPERATING']):
            return 'Active'
        elif any(k in s for k in ['PLUGGED', 'ABANDONED', 'NEVER DRILLED']):
            return 'Plugged / Abandoned'
        elif any(k in s for k in ['PERMITTED', 'ISSUED']):
            return 'Permitted / Undrilled'

    return 'Other / Unknown'

# ---------------------------------------------------------
# STATE BULK INGESTION ROUTINES
# ---------------------------------------------------------

def process_ny():
    print("Ingesting New York Master File...")
    url = "https://data.ny.gov/api/views/3ub5-233v/rows.csv?accessType=DOWNLOAD"
    try:
        res = requests.get(url, headers=HEADERS, timeout=60)
        df = pd.read_csv(io.BytesIO(res.content), low_memory=False)
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        
        out = pd.DataFrame()
        out['State'] = ['NY'] * len(df)
        out['Permit_ID'] = df['api_well_number'].astype(str)
        out['Well_Number'] = df['well_name'].fillna('Unknown').astype(str)
        out['Operator'] = df['operator_name'].fillna('Unknown Operator').astype(str)
        out['County'] = df['county'].fillna('Unknown').astype(str)
        out['Type'] = df['well_type'].fillna('Unknown').astype(str)
        out['Status'] = df['well_status'].fillna('Unknown').astype(str)
        out['Status_Category'] = out['Status'].apply(lambda x: normalize_status('NY', x))
        return out
    except Exception as e:
        print(f"NY Ingestion Failed: {e}")
        return pd.DataFrame(columns=TARGET_COLS)

def process_pa():
    print("Ingesting Pennsylvania Master File...")
    # PA DEP Bulk CSV Download Endpoint
    url = "https://www.depgreenport.state.pa.us/elibrary/GetFolder?FolderID=4559"
    # Alternative direct Open GIS master query limit override
    url_gis = "https://gis.dep.pa.gov/depgisprd/rest/services/OilGas/OilGasAllStrayGas/MapServer/3/query"
    try:
        # Fallback to full paginated harvest if elibrary requires session cookie
        all_recs = []
        offset = 0
        while offset < 100000: # Harvest up to 100k
            params = {'where': '1=1', 'outFields': '*', 'resultOffset': offset, 'resultRecordCount': 2000, 'f': 'json'}
            r = requests.get(url_gis, params=params, headers=HEADERS, timeout=30).json()
            feats = r.get('features', [])
            if not feats: break
            all_recs.extend([f['attributes'] for f in feats])
            offset += 2000
        
        df = pd.DataFrame(all_recs)
        out = pd.DataFrame()
        out['State'] = ['PA'] * len(df)
        out['Permit_ID'] = df['PERMIT_NUMBER'].astype(str)
        out['Well_Number'] = df['WELL_NUMBER'].fillna('Unknown').astype(str)
        out['Operator'] = df['OPERATOR_NAME'].fillna('Unknown Operator').astype(str)
        out['County'] = df['COUNTY'].fillna('Unknown').astype(str)
        out['Type'] = df['WELL_TYPE'].fillna('Unknown').astype(str)
        out['Status'] = df['WELL_STATUS'].fillna('Unknown').astype(str)
        out['Status_Category'] = out['Status'].apply(lambda x: normalize_status('PA', x))
        return out
    except Exception as e:
        print(f"PA Ingestion Failed: {e}")
        return pd.DataFrame(columns=TARGET_COLS)

def process_oh():
    print("Ingesting Ohio Master File...")
    url = "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/Oil_and_Gas_Wells_Locations_of_Ohio/FeatureServer/0/query"
    try:
        all_recs = []
        offset = 0
        while offset < 100000:
            params = {
                'where': '1=1',
                'outFields': 'PERMIT_NBR,WELL_NUMBER,OWNER_NAME,COUNTY,WELL_TYPE,WELL_STATUS',
                'resultOffset': offset,
                'resultRecordCount': 2000,
                'returnGeometry': 'false',
                'f': 'json'
            }
            r = requests.get(url, params=params, headers=HEADERS, timeout=30).json()
            feats = r.get('features', [])
            if not feats: break
            all_recs.extend([f['attributes'] for f in feats])
            offset += 2000

        df = pd.DataFrame(all_recs)
        out = pd.DataFrame()
        out['State'] = ['OH'] * len(df)
        out['Permit_ID'] = df['PERMIT_NBR'].astype(str)
        out['Well_Number'] = df['WELL_NUMBER'].fillna('Unknown').astype(str)
        out['Operator'] = df['OWNER_NAME'].fillna('Unknown Operator').astype(str)
        out['County'] = df['COUNTY'].fillna('Unknown').astype(str)
        out['Type'] = df['WELL_TYPE'].fillna('Unknown').astype(str)
        out['Status'] = df['WELL_STATUS'].fillna('Unknown').astype(str)
        out['Status_Category'] = out['Status'].apply(lambda x: normalize_status('OH', x))
        return out
    except Exception as e:
        print(f"OH Ingestion Failed: {e}")
        return pd.DataFrame(columns=TARGET_COLS)

if __name__ == "__main__":
    ny = process_ny()
    pa = process_pa()
    oh = process_oh()
    
    master_df = pd.concat([ny, pa, oh], ignore_index=True)
    master_df.to_parquet("wells_master.parquet", index=False)
    print(f"\n🚀 SUCCESS! Compiled {len(master_df):,} total verified wells into wells_master.parquet.")
