"""
JRHB Water Testing


"""

import os
import pandas as pd
from pandas import read_csv, to_datetime, DataFrame
#import numpy as np
from slugify import Slugify
from jinja2 import Environment, FileSystemLoader
from PIL import Image, ImageChops

# Custom modules
from WaterTesting.plotting import StackedArea, LinePlot

# Directories
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_ROOT = os.path.join(THIS_DIR, 'html')
LOC_PATH = 'location'
ABS_LOC_PATH = os.path.join(HTML_ROOT, LOC_PATH)
LOC_REPORT = 'report'
ABS_REPORT_PATH = os.path.join(HTML_ROOT, LOC_REPORT)

SLUG = Slugify(to_lower=True)


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


def build_source_summary(df, location, img_path):
    page_dict = {
        'caption': df['sample_location'].unique()[0],
        'slug': SLUG(location)
    }

    ## Water hardness plot
    x_data = df['sample_date']
    series = ['ca_hardness', 'mg_hardness', 'total_hardness']
    y_data = [df[col] for col in series]
    ids = df['sample_id']

    plot = LinePlot(
        x_data,
        y_data,
        series,
        ids,
        page_dict['slug'] + '-hardness'
    )

    png, js = plot.plot(img_path)
    trim(os.path.join(img_path, png))

    page_dict['hardness_png'] = png




    ## Alkalinity over time (Total, Residual)
    series = ['total_alkalinity', 'res_alkalinity']
    y_data = [df[col] for col in series]
    ids = df['sample_id']

    my_plot = LinePlot(
        x_data,
        y_data,
        series,
        ids,
        page_dict['slug'] + '-alkalinity'
    )

    png, js = my_plot.plot(img_path)
    trim(os.path.join(img_path, png))

    page_dict['alkalinity_png'] = png

    

    ## Ion Concentrations over time (Cl-, SO4-, Ca2+, Mg2+, HCO3-)
    ion_list = [
        ('cl', 'Chlorine'),
        ('so4', 'Sulfate'),
        ('ca2', 'Calcium'),
        ('mg2', 'Magnesium'),
        ('hco3', 'Bicarbonate'),
    ]

    page_dict['ion_png_list'] = []
    page_dict['ion_html_list'] = []

    for ion in ion_list:
        my_plot = LinePlot(
            x_data,
            [df[ion[0]]],
            [ion[1]],
            ids,
            page_dict['slug'] + '-' + ion[0]
        )

        png, js = my_plot.plot(img_path, legend=False)
        trim(os.path.join(img_path, png))

        page_dict['ion_png_list'].append([png, ion[1]])
        page_dict['ion_html_list'].append([js, ion[1]])

    ## pH over time


    return page_dict


if __name__ == '__main__':
    # Set HTML template files
    loc_tmpl = os.path.join('templates', 'bootstrap_summary_sheet.html')
    index_tmpl = os.path.join('templates', 'bootstrap_base.html')
    report_tmpl = os.path.join('templates', 'report.html')

    df = gsload.load_sheet(
        'client_id.json',
        '1Z1XF9nabneWBDbFwaovI_n9YcazeNQq4hon1wsIxrus',
        'Data'
    )

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
