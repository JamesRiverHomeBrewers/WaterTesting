"""
Module for loading data form google sheets and dumping it 
into a pandas dataframe.

"""
import pandas as pd
from pandas import read_csv, to_datetime, DataFrame
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from slugify import Slugify

SLUG = Slugify(to_lower=True)

SO4CL_RATIO = {
    0: 'Too Malty',
    0.4: 'Very Malty',
    .6: 'Malty',
    .8: 'Balanced',
    1.5: 'Little Bitter',
    2.01: 'More Bitter',
    4.01: 'Extra Bitter',
    6.01: 'Quite Bitter',
    8.01: 'Very Bitter',
    9.01: 'Too Bitter'
}


def add_columns(df):
    """ Add calculated columns to the dataframe

        Accepts test result dataframe and return the newly modified dataframe.

    """
    # Rename columns from google sheets
    df = df.rename(columns={
        'Sample ID':            'sample_id',
        'Sample Date':          'sample_date',
        'Sample Source':        'sample_source',
        'Sample Treatment':     'treatment',
        'Sample Notes':         'notes',
        'Test Date':            'test_date',
        'Sample Location':      'sample_location',
        'Total Hardness':       'total_hardness',
        'Calcium Hardness':     'ca_hardness',
        'Total Alkalinity':     'total_alkalinity',
        'Sulfate':              'so4',
        'Chlorine':             'cl',
    })

    # Everything is loaded as strings, need to convert to numeric
    df['total_hardness'] = df['total_hardness'].apply(pd.to_numeric, args=('coerce',))
    df['ca_hardness'] = df['ca_hardness'].apply(pd.to_numeric, args=('coerce',))
    df['total_alkalinity'] = df['total_alkalinity'].apply(pd.to_numeric, args=('coerce',))
    df['so4'] = df['so4'].apply(pd.to_numeric, args=('coerce',))
    df['cl'] = df['cl'].apply(pd.to_numeric, args=('coerce',))

    # Add calculated columns
    df['mg_hardness'] = df['total_hardness'] - df['ca_hardness']
    df['res_alkalinity'] = df['total_alkalinity'] - (df['ca_hardness'] / 3.5 + df['mg_hardness'] / 7)
    df['ca2'] = df['ca_hardness'] * 0.4
    df['mg2'] = df['mg_hardness'] * 0.25
    df['hco3'] = df['total_alkalinity'] * 1.22
    df['so4_cl_ratio'] = df['so4'] / df['cl']

    # Add descriptor from SO4 / Cl Ratio Lookup
    set_ratio = [min(SO4CL_RATIO.keys(), key=lambda x: abs(x - r)) for r in df['so4_cl_ratio']]
    ratios = [SO4CL_RATIO[value] for value in set_ratio]

    df['balance'] = ratios

    df['sample_date'] = to_datetime(df['sample_date'], format='%m/%d/%Y').dt.date
    df['test_date'] = to_datetime(df['test_date'], format='%m/%d/%Y').dt.date

    df['slug'] = [SLUG(x) for x in df['sample_location']]

    df = df.sort_values(by='sample_date')

    df = df.round(2)

    return df


def load_csv(filename):
    df = read_csv(filename)
    df = add_columns(df)

    return df


def load_sheet(key, sheet_id, sheet_tab):
    """ Connect to a google spreadsheet using gspread and load it
        into a dataframe.

        Parameters:
          key: json key file from google developer console
          sheet_id: ID of the sheet found in the sheet URL
          sheet_tab: name of the tab within the worksheet to pull

        Return: gspread worksheet object
    """

    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(key, scope)
    gc = gspread.authorize(credentials)

    wks = gc.open_by_key(sheet_id).worksheet(sheet_tab)

    # Dump spreadsheet data into dataframe and add calculated columns
    df = DataFrame(wks.get_all_records())
    df = add_columns(df)
    
    return df
