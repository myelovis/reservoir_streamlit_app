import pandas as pd
import streamlit as st

@st.cache_data
def load_data(filepath: str = "reservoirs.csv") -> pd.DataFrame:
    """Reads reservoir CSV data, renames headers to English, and formats timestamps."""
    df = pd.read_csv(filepath)

    # Rename headers from Norwegian to English
    rename_dict = {
        'dato_Id': 'date_id',
        'omrType': 'area_type',
        'omrnr': 'area_number',
        'iso_aar': 'iso_year',
        'iso_uke': 'iso_week',
        'fyllingsgrad': 'fill_ratio',
        'kapasitet_TWh': 'capacity_twh',
        'fylling_TWh': 'storage_twh',
        'neste_Publiseringsdato': 'next_publication_date',
        'fyllingsgrad_forrige_uke': 'fill_ratio_previous_week',
        'endring_fyllingsgrad': 'fill_ratio_change',
    }
    df = df.rename(columns=rename_dict)

    # Convert date column to datetime and sort chronologically
    if 'date_id' in df.columns:
        df['date_id'] = pd.to_datetime(df['date_id'], errors='coerce')
        df = df.sort_values(by='date_id').reset_index(drop=True)

    return df