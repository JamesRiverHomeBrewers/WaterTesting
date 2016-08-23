from flask import render_template
from WaterTesting import app

# Load test result data
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
@app.route('/index')
def index():
    return "Hello, World!"


# Setting route to test result
@app.route('/result/<int:sample_id>')
def result(sample_id):
    test_result = df[df['sample_id'] == sample_id]

    if test_result.empty:
        flash('Test result {} not found.'.format(sample_id))
        return redirect(url_for('index'))

    report = test_result.to_dict('records')[0]
    print(report)
    return render_template('report.html', report=report )


# Setting route to location summary page with plots
@app.route('/location/<location>')
def summary(location):
    loc_df = df[df['sample_location'] == location]

    # build_source_summary() needs to return a dictionary with image filenames
    # plus any additional metadata to be used on the page.
    summary = build_source_summary(loc_df)

    if summary   == None:
        flash('Location data not found for {}.'.format(location))
        return redirect(url_for('index'))

    return render_template('location.html', summary=summary )
