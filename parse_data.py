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
LOCATION_DIR = 'location'
ABS_LOCATION_DIR = os.path.join(HTML_ROOT, 'location')

SLUG = UniqueSlugify(to_lower=True)



def trim(path):
	im = Image.open(path)

	bg = Image.new(im.mode, im.size, im.getpixel((0,0)))
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


if __name__ == '__main__':
	scope = ['https://spreadsheets.google.com/feeds']
	credentials = ServiceAccountCredentials.from_json_keyfile_name('client_id.json', scope)
	gc = gspread.authorize(credentials)
	wks = gc.open_by_key("1Z1XF9nabneWBDbFwaovI_n9YcazeNQq4hon1wsIxrus").worksheet('Data')
	df = DataFrame(wks.get_all_records())

	loc_tmpl = os.path.join('templates', 'bootstrap_summary_sheet.html')
	index_tmpl = os.path.join('templates', 'bootstrap_base.html')
	print(df.columns.values)
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

	# Everything is loaded as strings, need to convert to numeric
	df['Total Hardness'] = df['Total Hardness'].apply(pd.to_numeric, args=('coerce',))
	df['Calcium Hardness'] = df['Calcium Hardness'].apply(pd.to_numeric, args=('coerce',))
	df['Total Alkalinity'] = df['Total Alkalinity'].apply(pd.to_numeric, args=('coerce',))
	df['Sulfate'] = df['Sulfate'].apply(pd.to_numeric, args=('coerce',))
	df['Chlorine'] = df['Chlorine'].apply(pd.to_numeric, args=('coerce',))

	# Add calculated columns
	df['Magnesium Hardness'] = df['Total Hardness'] - df['Calcium Hardness']
	df['Residual Alkalinity'] = df['Total Alkalinity'] - (df['Calcium Hardness']/3.5 + df['Magnesium Hardness']/7)
	df['ca2'] = df['Calcium Hardness'] * 0.4
	df['mg2'] = df['Magnesium Hardness'] * 0.25
	df['hco3'] = df['Total Alkalinity'] * 1.22
	df['so4_cl_ratio'] = df['Sulfate'] / df['Chlorine']

	# Add descriptor from SO4 / Cl Ratio Lookup
	set_ratio = [min(SO4CL_RATIO.keys(), key=lambda x: abs(x - r)) for r in df['so4_cl_ratio']]
	ratios = [SO4CL_RATIO[value] for value in set_ratio]
	
	df['balance'] = ratios
	df['Sample Date'] = to_datetime(df['Sample Date'], format='%Y-%m-%d')
	df = df.sort_values(by='Sample Date')

	locations = df['Sample Location'].unique()

	pages = []

	# Headings:
	#  total_hardness, ca_hardness, mg_hardness
	#  Total Alkalinity, res_alkalinity
	#  cl, so4, ca2, mg2, hco3                            Ion Concentrations
	#  so4_cl                                             SO4/Cl ratio
	#  ph
	for location in locations:
		page_dict = {'caption': location}
		page_dict['slug'] = SLUG(location)
		page_dict['src'] = os.path.join(ABS_LOCATION_DIR, page_dict['slug'] + '.html')
		page_dict['url'] = LOCATION_DIR + '/' + page_dict['slug'] + '.html'

		filtered = df[df['Sample Location'] == location]

		## Hardness over time (Total, Ca, Mg)
		my_plot = LinePlot(
			filtered['Sample Date'],
			[filtered['Calcium Hardness'], filtered['Magnesium Hardness']],
			['Ca Hardness', 'Mg Hardness'],
			filtered['Sample ID'],
			page_dict['slug'] + '-hardness'
		)

		page_dict['hardness_plt_png'], page_dict['hardness_plt_html'] = my_plot.plot()
		page_dict['hardness_plt_png'] = os.path.join(
			'..',
			'img',
			page_dict['hardness_plt_png']
		)
		trim(os.path.join('html', 'img', page_dict['hardness_plt_png']))
		## Alkalinity over time (Total, Residual)

		## Ion Concentrations over time (Cl-, SO4-, Ca2+, Mg2+, HCO3-)
		ion_list = [
			('Chlorine', 'Cl-'),
			('Sulfate', 'SO4-'),
			('ca2', 'Ca2+'),
			('mg2', 'Mg2+'),
			('hco3', 'HCO3-'),
		]
		dates = filtered['Sample Date']
		ids = filtered['Sample ID']

		page_dict['ion_png'] = []
		page_dict['ion_html'] = []

		for ion in ion_list:
			my_plot = LinePlot(
				dates,
				[filtered[ion[0]]],
				[ion[1]],
				ids,
				page_dict['slug'] + '-' + ion[0]
			)

			png, html = my_plot.plot()

			trim(os.path.join('html', 'img', png))

			png = os.path.join('..', 'img', png)

			page_dict['ion_png'].append([png, ion[1]])
			page_dict['ion_html'].append(html)

		## SO4/Cl Ratio over time

		## pH over time

		pages.append(page_dict)

	## Write Location Pages
	for page in pages:
		if page['slug'] != 'Home':
			with open(page['src'], 'w') as html_file:
				html_file.write(make_html_doc(loc_tmpl, {'thispage': page, 'pages': pages}))

	## Make main index
	with open(HTML_ROOT + '/index.html', 'w') as html_file:
		html_file.write(make_html_doc(index_tmpl, {'pages': pages}))

