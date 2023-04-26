from flask import Flask, render_template, request, url_for, redirect, session
from models import Event, Place, CATEGORIES
from datetime import datetime
import locale
from markdown import markdown
from collections import defaultdict
from werkzeug.security import check_password_hash
from settings import USERS, SECRET_KEY
from flask_httpauth import HTTPBasicAuth


locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
app = Flask(__name__)
app.secret_key = SECRET_KEY
auth = HTTPBasicAuth()


def md(some_text):
    return markdown(some_text, extensions=['nl2br'])

@app.context_processor
def inject_md():
    return dict(md=md)

@auth.verify_password
def verify_password(username, password):
    if username in USERS and check_password_hash(USERS[username], password):
        session['username'] = username
        return username

@app.route("/login")
@auth.login_required
def login():
    session['admin'] = True
    return redirect(url_for('index'))

@app.route("/logout")
@auth.login_required
def logout():
    del session['admin']
    return redirect(url_for('index'))

    
@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


def _default_filter(events):
    return events.where(
        # multiple days events
        (Event.date_end >= datetime.now()) |
        # regular events
        ((Event.date_start >= datetime.now()) & Event.date_end.is_null()) |        
        # perpetual events ?
        (Event.date_start.is_null()))

@app.route("/last_created")
def last_created():
    events = Event.select().where(Event.creation_date.is_null(False))
    events = _default_filter(events)
    events = events.order_by(Event.creation_date.desc()).limit(200)
    return render_template("last_added.html", events=events)

@app.route("/category/<name>/")
def category(name):
    conditions = []
    events = Event.select().where(Event.category == name)
    events = _default_filter(events)
    if name == 'expositions':
        events = events.order_by(Event.date_end.asc())
    else:
        events = events.order_by(Event.date_start.asc())
    months = defaultdict(lambda: defaultdict(list))
    for event in events:
        if event.date_start:
            months[event.date_start.strftime('%B')][event.date_start].append(event.id)
    return render_template(
        'category.html',
        events=events,
        category=name,
        category_label=CATEGORIES[name],
        months=months)

@app.route("/admin/places/")
@auth.login_required
def places():
    places = Place.select().order_by(Place.name.asc())
    return render_template('places.html', places=places)

@app.route("/admin/place_new/", methods=['GET', 'POST'])
@app.route("/admin/place_edit/<int:place_id>/", methods=['GET', 'POST'])
@auth.login_required
def place_edit(place_id=None):
    if request.method == 'POST':
        if request.form['place_id']:
            query = Place.update({
                'name': request.form['name'],
                'description': request.form['description']
            }).where(Place.id == request.form['place_id'])
            query.execute()
        else:
            Place.create(name=request.form['name'],
                         description=request.form['description'])
        return redirect(url_for('places'))
    place = None
    if place_id:
        place = Place.get(Place.id == place_id)
    return render_template('place_edit.html', place=place)


@app.route("/delete/<event_id>/")
def delete(event_id):
    Event.get(Event.id == event_id).delete_instance()
    return "Event deleted"

@app.route("/edit/<int:event_id>/", methods=['GET', 'POST'])
@app.route("/new/<category>/", methods=['GET', 'POST'])
@app.route("/new/<int:orig_event_id>/", methods=['GET', 'POST'])
@app.route("/new/", methods=['GET', 'POST'])
@auth.login_required
def edit(event_id=None, category='concerts', orig_event_id=None):
    if request.method == 'POST':
        values = {k: request.form[k] for k in ['category',
                                               'time_details',
                                               'place',
                                               'description',
                                               'price',
                                               'external_link',
                                               'created_by']}
        values['highlight'] = True if 'highlight' in request.form else False
        if request.form['date_start']:
            values['date_start'] = datetime.fromisoformat(request.form['date_start']).date()
        else:
            values['date_start'] = None
        if request.form['date_end']:
            values['date_end'] = datetime.fromisoformat(request.form['date_end']).date()
        else:
            values['date_end'] = None
        if request.form['event_id']:
            query = Event.update(
                values
            ).where(Event.id == request.form['event_id'])
            query.execute()
        else:
            Event.create(**values)
        return redirect(url_for('category', name=request.form['category']))
    
    event = None
    if event_id or orig_event_id:
        event = Event.get(Event.id == (event_id or orig_event_id))
        category = event.category
    return render_template(
        'edit.html',
        categories=CATEGORIES,
        category=category,
        event=event,
        places=Place.select().order_by(Place.name.asc()),
        duplicate=True if orig_event_id else False)


@app.route("/api/place/<int:place_id>/")
def read_place(place_id):
    if place_id == 0:
        return ''
    place = Place.get(Place.id == place_id)
    return place.description
