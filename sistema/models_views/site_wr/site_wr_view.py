from sistema import app
from flask import render_template


@app.route('/', methods=['GET'])
def index_page():
    return render_template('site_wr/index.html')
