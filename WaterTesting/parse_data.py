"""
JRHB Water Testing


"""

import os
import pandas as pd
from pandas import read_csv, to_datetime, DataFrame
#import numpy as np
from slugify import Slugify
from jinja2 import Environment, FileSystemLoader


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

    page_dict['hardness_png'] = png
    page_dict['hardness_js'] = js



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

    page_dict['alkalinity_png'] = png
    page_dict['alkalinity_js'] = js

    ## Ion Concentrations over time (Cl-, SO4-, Ca2+, Mg2+, HCO3-)
    ion_list = [
        ('cl', 'Chlorine'),
        ('so4', 'Sulfate'),
        ('ca2', 'Calcium'),
        ('mg2', 'Magnesium'),
        ('hco3', 'Bicarbonate'),
    ]

    page_dict['ion_png_list'] = []
    page_dict['ion_js_list'] = []

    for ion in ion_list:
        my_plot = LinePlot(
            x_data,
            [df[ion[0]]],
            [ion[1]],
            ids,
            page_dict['slug'] + '-' + ion[0]
        )

        png, js = my_plot.plot(img_path, legend=False)

        page_dict['ion_png_list'].append([png, ion[1]])
        page_dict['ion_js_list'].append([js, ion[1]])

    ## pH over time


    return page_dict
