"""
JRHB Water Testing


"""

import os
from pandas import read_csv
from pandas import to_datetime
import numpy as np
from slugify import UniqueSlugify
from jinja2 import Environment, FileSystemLoader

from plotting import StackedArea, LinePlot

# Directories
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_ROOT = os.path.join(THIS_DIR, 'html')
LOCATION_DIR = os.path.join(HTML_ROOT, 'location')

SLUG = UniqueSlugify(to_lower=True)

def make_html_doc(template, content):
    # Create the jinja2 environment.
    j2_env = Environment(loader=FileSystemLoader(THIS_DIR),
                         trim_blocks=True)
    return j2_env.get_template(template).render(content)


if __name__ == '__main__':
	df = read_csv('data.csv')


	loc_tmpl = os.path.join('templates', 'summary_sheet.html')

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

	# Add calculated columns
	df['mg_hardness'] = df['total_hardness'] - df['ca_hardness']
	df['res_alkalinity'] = df['total_alkalinity'] - (df['ca_hardness']/3.5 + df['mg_hardness']/7)
	df['ca2'] = df['ca_hardness'] * 0.4
	df['mg2'] = df['mg_hardness'] * 0.25
	df['hco3'] = df['total_alkalinity'] * 1.22
	df['so4_cl'] = df['so4'] / df['cl']

	# Add descriptor from SO4 / Cl Ratio Lookup
	set_ratio = [min(SO4CL_RATIO.keys(), key=lambda x: abs(x - r)) for r in df['so4_cl']]
	ratios = [SO4CL_RATIO[value] for value in set_ratio]

	df['balance'] = ratios

	df['sample_date'] = to_datetime(df['sample_date'])
	df = df.sort_values(by='sample_date')

	locations = df.charting.unique()

	pages = []

	for location in locations:
		page_dict = {'page_title': location}
		loc_slug = SLUG(location)
		filtered = df[df.charting == location]

		## Hardness over time (Total, Ca, Mg)
		my_plot = LinePlot(
			filtered['sample_date'],
			[filtered['ca_hardness'], filtered['mg_hardness']],
			['Ca Hardness', 'Mg Hardness'],
			filtered.id,
			loc_slug
		)

		page_dict['hardness_plt_png'], page_dict['hardness_plt_html'] = my_plot.plot()

		html_path = os.path.join(THIS_DIR, HTML_ROOT, LOCATION_DIR, loc_slug + '.html')

		## Alkalinity over time (Total, Residual)

		## Ion Concentrations over time (Cl-, SO4-, Ca2+, Mg2+, HCO3-)

		## SO4/Cl Ratio over time

		## pH over time

		with open(html_path, 'w') as html_file:
			html_file.write(make_html_doc(loc_tmpl, page_dict))

		pages.append(page_dict)
