
import os
from flask import render_template
from slugify import Slugify

from WaterTesting import app
from WaterTesting.parse_data import build_source_summary

#~ import flask, flask_frozen
#~ flask.url_for = flask_frozen.url_for

ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
SLUG = Slugify(to_lower=True)

#~ # Load test result data
if app.config['TESTING'] == True:
    from WaterTesting.gsload import load_csv
    df = load_csv(app.config['DATA_FILE'])

else:
    from WaterTesting.gsload import load_sheet
    
    df = load_sheet(
        app.config['GOOGLE_API_KEY'],
        app.config['GOOGLE_SHEET_ID'],
        app.config['GOOGLE_SHEET_TAB']
    )

@app.route('/')
def index():
    recent = df.tail(n=5)
    recent = recent.sort_values(by='sample_date', ascending=False)
    recent = recent.to_dict('records')
    return render_template('index.html', recent=recent )


# Setting route to test result
@app.route('/result/<int:sample_id>/')
def result(sample_id):
    test_result = df[df['sample_id'] == sample_id]

    if test_result.empty:
        flash('Test result {} not found.'.format(sample_id))
        return redirect(url_for('index'))

    report = test_result.to_dict('records')[0]

    return render_template('report.html', report=report )


# Setting route to test result
@app.route('/result/index/')
def result_index():
    return 'ToDo'

# Setting route to location summary page with plots
@app.route('/location/<location>/')
def summary(location):
    img_dir = os.path.join(ROOT_DIR, 'static', 'img')

    loc_df = df[df["slug"] == location]
    
    locations = [(SLUG(x), x) for x in df['sample_location'].unique()]

    #loc_df = df[df['sample_location'] == location]

    # build_source_summary() needs to return a dictionary with image filenames
    # plus any additional metadata to be used on the page.
    summary = build_source_summary(loc_df, location, img_dir)

    if summary == None:
        flash('Location data not found for {}.'.format(location))
        return redirect(url_for('index'))

    return render_template('location.html', summary=summary, pages=locations )
