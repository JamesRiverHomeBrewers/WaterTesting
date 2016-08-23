"""
JRHB Water Testing


"""

import os
import pandas as pd
from pandas import read_csv, to_datetime, DataFrame
import numpy as np
from slugify import UniqueSlugify
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageChops
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from plotting import StackedArea, LinePlot

# Directories
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_ROOT = os.path.join(THIS_DIR, 'html')
LOC_PATH = 'location'
ABS_LOC_PATH = os.path.join(HTML_ROOT, LOC_PATH)
LOC_REPORT = 'report'
ABS_REPORT_PATH = os.path.join(HTML_ROOT, LOC_REPORT)

SLUG = UniqueSlugify(to_lower=True)

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


def trim(path):
    im = Image.open(path)

    bg = Image.new(im.mode, im.size, im.getpixel((0, 0)))
    diff = ImageChops.difference(im, bg)
    diff = ImageChops.add(diff, diff, 2.0, -100)
    bbox = diff.getbbox()
    if bbox:
        im.save(path)


def make_html_doc(template, content):
    # Create the jinja2 environment.
    j2_env = Environment(loader=FileSystemLoader(THIS_DIR),
                         trim_blocks=True)
    return j2_env.get_template(template).render(content)


def add_columns(df):
    """ Add calculated columns to the dataframe

        Accepts test result dataframe and return the newly modified dataframe.

    """
    # Rename columns from google sheets
    df = df.rename(columns={
        'Sample ID': 'sample_id',
        'Sample Date': 'sample_date',
        'Sample Source': 'sample_source',
        'Source if "Other"': 'source_other',
        'Sample Treatment': 'treatment',
        'Sample Notes': 'notes',
        'Treatment if "Other"': 'treatment_other',
        'Test Date': 'test_date',
        'Sample Location': 'sample_location',
        'Total Hardness': 'total_hardness',
        'Calcium Hardness': 'ca_hardness',
        'Total Alkalinity': 'total_alkalinity',
        'Sulfate': 'so4',
        'Chlorine': 'cl',
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

    df = df.sort_values(by='sample_date')

    df = df.round(2)

    return df


def connect_sheets(key, sheet_id, sheet_tab):
    """ Connect to a google spreadsheet using gspread

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

    return wks

def build_source_summaries(df, locations):
    source_pages = []

    for location in locations:
        page_dict = {'caption': location}
        page_dict['slug'] = SLUG(location)
        page_dict['src'] = os.path.join(
            ABS_LOC_PATH, page_dict['slug'] + '.html'
        )
        page_dict['url'] = LOC_PATH + '/' + page_dict['slug'] + '.html'

        filtered = df[df['sample_location'] == location]

        ## Hardness over time (Total, Ca, Mg)
        x_data = filtered['sample_date']
        series = ['ca_hardness', 'mg_hardness', 'total_hardness']
        y_data = [filtered[col] for col in series]
        ids = filtered['sample_id']

        my_plot = LinePlot(
            x_data,
            y_data,
            series,
            ids,
            page_dict['slug'] + '-hardness'
        )

        png, html = my_plot.plot()

        # Relative path for source locatin pages
        page_dict['hardness_png'] = os.path.join('..', 'img', png)

        trim(os.path.join('html', 'img', page_dict['hardness_png']))

        ## Alkalinity over time (Total, Residual)
        series = ['total_alkalinity', 'res_alkalinity']
        y_data = [filtered[col] for col in series]
        ids = filtered['sample_id']

        my_plot = LinePlot(
            x_data,
            y_data,
            series,
            ids,
            page_dict['slug'] + '-alkalinity'
        )

        png, html = my_plot.plot()

        # Relative path for source locatin pages
        page_dict['alkalinity_png'] = os.path.join('..', 'img', png)

        trim(os.path.join('html', 'img', page_dict['alkalinity_png']))

        ## Ion Concentrations over time (Cl-, SO4-, Ca2+, Mg2+, HCO3-)
        ion_list = [
            ('cl', 'Chlorine'),
            ('so4', 'Sulfate'),
            ('ca2', 'Calcium'),
            ('mg2', 'Magnesium'),
            ('hco3', 'Bicarbonate'),
        ]

        page_dict['ion_png'] = []
        page_dict['ion_html'] = []

        for ion in ion_list:
            my_plot = LinePlot(
                x_data,
                [filtered[ion[0]]],
                [ion[1]],
                ids,
                page_dict['slug'] + '-' + ion[0]
            )

            png, html = my_plot.plot(legend=False)

            trim(os.path.join('html', 'img', png))

            png = os.path.join('..', 'img', png)
            page_dict['ion_png'].append([png, ion[1]])
            page_dict['ion_html'].append(html)

        ## pH over time

        source_pages.append(page_dict)

    return source_pages


if __name__ == '__main__':
    # Set HTML template files
    loc_tmpl = os.path.join('templates', 'bootstrap_summary_sheet.html')
    index_tmpl = os.path.join('templates', 'bootstrap_base.html')
    report_tmpl = os.path.join('templates', 'report.html')

    # Connect to Google spreadsheet
    worksheet = connect_sheets(
        'client_id.json',
        '1Z1XF9nabneWBDbFwaovI_n9YcazeNQq4hon1wsIxrus',
        'Data'
    )

    # Dump spreadsheet data into dataframe and add calculated columns
    df = DataFrame(worksheet.get_all_records())
    df = add_columns(df)

    # List of water sources
    locations = df['sample_location'].unique()

    source_pages = build_source_summaries(df, locations)

    # Convet dataframe to list of dicts for individual records
    report_pages = df.to_dict('records')

    # Get most recent test for main page
    recent = df.tail(n=5)
    recent = recent.sort_values(by='sample_date', ascending=False)
    recent = recent.to_dict('records')

    ## Write location source pages
    # source_page keys:
    #   caption            Page title: Used for page headings
    #   slug               Page slug: Not used
    #   src                Source file path: Used for file creation
    #   url                URL relative to index: Used for page links
    #   hardness_png       Hardness plot filename: Used for image links
    #   hardness_html      Hardness plot HTML from mpld3: Not used
    #   ion_png            List of Ion plot filenames: Used for image links
    #   ion_html           Not used

    for page in source_pages:
        with open(page['src'], 'w') as html_file:
            html_file.write(make_html_doc(loc_tmpl, {
                'thispage': page,
                'pages': source_pages
            }))

    for page in report_pages:
        page_path = os.path.join(ABS_REPORT_PATH, str(page['sample_id']) + '.html')
        with open(page_path, 'w') as html_file:
            html_file.write(make_html_doc(report_tmpl, {
                'thispage': page,
            }))

    ## Make main index
    with open(HTML_ROOT + '/index.html', 'w') as html_file:
        html_file.write(make_html_doc(index_tmpl, {
            'source_pages': source_pages,
            'recent': recent,
        }))
