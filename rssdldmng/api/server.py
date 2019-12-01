import logging
import json
import copy

from threading import Thread

log = logging.getLogger(__name__)

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    abort,
    flash,
    redirect
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, PasswordField, SelectField, IntegerField, BooleanField, SubmitField, FieldList, FormField
from wtforms.validators import DataRequired, URL, NumberRange, Optional

app = Flask(__name__, static_folder="./static", template_folder="./templates")
app.config['SECRET_KEY'] = 'you-will-never-guess'
CSRFProtect(app)

class ApiServer():
    def __init__(self, port, mng):
        self.port = port
        app.manager = mng

    def serve_forever(self):
        app.run(debug=True, use_reloader=False, host='0.0.0.0', port=self.port)

    def start(self):
        self.server = Thread(target=self.serve_forever)
        self.server.daemon = True
        self.server.start()
        log.info('Started HTTP server at {0}'.format(self.port))

    def stop(self):
        #self.server.terminate()
        #self.server.join()
        log.info('Stopped HTTP server')

def encodeJson(content):
    try:
        return json.dumps(content).encode('utf-8')
    except TypeError:
        return json.dumps(content, default=lambda x: x.__dict__).encode('utf-8')

import collections.abc

def dict_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = dict_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

# FORMS

class AddFeedForm(FlaskForm):
    feed = StringField('Feed', validators=[URL()])
    quality = SelectField('Quality', choices=[('', 'any'), ('720p', '720p'), ('1080p', '1080p')])
    season = IntegerField('Season', validators=[Optional(), NumberRange(0, 99)])
    submit = SubmitField('Parse Feed')

class FiltersConfigForm(FlaskForm):
    quality = FieldList(SelectField('Quality filter', choices=[('', 'any'), ('720p', '720p'), ('1080p', '1080p')]))
    series = StringField('Show List')

class TraktConfigForm(FlaskForm):
    clientid = StringField('Client ID')
    clientsecret = StringField('Client secret')
    username = StringField('Username')
    tmdbapikey = StringField('TMDB Api key')

class RemoteServerConfigForm(FlaskForm):
    host = StringField('Host')
    port = IntegerField('Port', validators=[NumberRange(1000, 65535)])
    username = StringField('Username')
    password = PasswordField('Password')

class ConfigForm(FlaskForm):
    dir = StringField('Download Folder')
    feeds = FieldList(StringField('Feed', validators=[URL()]))
    feed_poll_interval = IntegerField('Interval (seconds)', validators=[Optional(), NumberRange(0, 3000)])
    poll_interval = IntegerField('Interval (seconds)', validators=[Optional(), NumberRange(0, 3000)])

    filters = FormField(FiltersConfigForm)
    trakt = FormField(TraktConfigForm)
    transmission = FormField(RemoteServerConfigForm)
    kodi = FormField(RemoteServerConfigForm)

    cancel = SubmitField('Cancel')
    submit = SubmitField('Save')


# CONTENT

@app.route('/')
@app.route('/recent')
def recent():
    log.debug('get / (retrive episodes)')
    eps = app.manager.get_latest(21)
    log.debug('get / (renter template)')
    return render_template('recent.html', title='Recent Episodes', episodes=eps)

@app.route('/shows')
def shows():
    series = app.manager.downloader.epFilter['series']
    return render_template('shows.html', title='Shows currently tracking', shows=series)

@app.route('/addfeed', methods=['GET', 'POST'])
def addfeed():
    form = AddFeedForm()
    if form.validate_on_submit():
        filter = {
            'quality': form.quality.data,
            'season': [form.season.data]
        }
        res = app.manager.downloader.parseFeed(form.feed.data, filter)
        flash('{}<hr>{}'.format(form.feed.data, res), category='Feed Added')
        return redirect('/')
    return render_template('addfeed.html', title='Add new feed for parsing', form=form)

@app.route('/config', methods=['GET', 'POST'])
def config():
    data = app.manager.config.downloader
    form = ConfigForm(obj=data)
    if 'submit' in request.form:
        if form.validate_on_submit():
            modified_data = copy.deepcopy(data)
            form.populate_obj(modified_data)
            delattr(modified_data, 'submit')
            delattr(modified_data, 'cancel')
            app.manager.config.downloader = copy.deepcopy(modified_data)
            app.manager.save_config()
            flash('Configuration saved. Restart the application.')
            return redirect('/')
    if 'cancel' in request.form:
        flash('Configuration modification canceled')
        return redirect('/')
    return render_template('config.html', title='Configuration' ,form=form)
