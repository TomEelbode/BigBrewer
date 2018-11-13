import pandas as pd
from flask import current_app, jsonify
from datetime import datetime, date, timedelta

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from BigBrewer.db import get_db

bp = Blueprint('ttn', __name__, url_prefix='/ttn')


# curl --header "Content-Type: application/json" --request POST --data '{"metadata": {"time": "2018-05-29T11:25:11.875464918Z"}, "app_id": "plantsensors", "port": 3, "dev_id": "plant1", "downlink_url": "https://integrations.thethingsnetwork.org/ttn-eu/api/v2/down/plantsensors/plantsensors?key=ttn-account-v2.03DrO-vnpemZkrPkhp4xzt8yZfOEHDEAv9bPIHFXaOE", "hardware_serial": "003C9E6CD0EB61F8", "payload_raw": "ZmZmZmZm", "payload_fields": {"voltage": 26.214, "plantname": "test", "water": 6710886}, "counter": 0}' 127.0.0.1:5000/ttn/submit

@bp.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        current_app.logger.info(request.get_json())
        data = request.get_json()

        metadata = data["metadata"]
        date = pd.to_datetime(metadata['time']).strftime('%Y-%m-%d %H:%M:%S')

        dev_id = data['dev_id']

        payload = data['payload_fields']
        water = payload['water']
        voltage = payload['voltage']
        db = get_db()
        error = None
        if not water:
            error = 'Water is required.'
        elif not voltage:
            error = 'Voltage is required.'

        plant_id = db.execute(
            'SELECT id FROM plant WHERE dev_id = ?', (dev_id,)
        ).fetchone()
        if plant_id is None:
            error = 'Device {} is not yet registered.'.format(dev_id)

        if error is None:
            db.execute(
                'INSERT INTO status (plant_id, water, voltage, date_tx)  VALUES (?, ?, ?, ?)',
                (plant_id[0], water, voltage, date)
            )
            db.commit()
        else:
            current_app.logger.warning(error)

    return request.query_string


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        plantname = request.form['plantname']
        dev_id = request.form['dev_id']
        location = request.form['location']
        color = request.form['color']
        db = get_db()
        error = None

        if not plantname:
            error = 'Plantname is required.'
        elif not dev_id:
            error = 'Device_id is required.'
        elif not location:
            error = 'Location is required.'
        elif not color:
            error = 'Color is required.'
        elif db.execute(
                'SELECT id FROM plant WHERE dev_id = ?', (dev_id,)
        ).fetchone() is not None:
            error = 'Device {} already exists.'.format(dev_id)
        elif db.execute(
                'SELECT id FROM plant WHERE color = ?', (color,)
        ).fetchone() is not None:
            error = 'Color {} is already in use.'.format(color)

        if error is None:
            db.execute(
                'INSERT INTO plant (dev_id, plantname, location, color) VALUES (?, ?, ?, ?)',
                (dev_id, plantname, location, color)
            )
            db.commit()
            return redirect(url_for('info.index'))

        flash(error)
        current_app.logger.warning(error)

    return render_template('ttn/register.html')


@bp.route('/data', methods=['GET'])
def get_data():
    db = get_db()
    c = db.cursor()
    plants = c.execute(
        'SELECT plantname, dev_id, color, location'
        ' FROM plant'
    ).fetchall()

    plants = [dict(zip([key[0] for key in c.description], row)) for row in plants]

    today = date.today()
    last_n_days = 7
    day_offset = today - timedelta(days=last_n_days)
    month_ago = today - timedelta(days=31)
    water = dict()
    for plant in plants:
        max_water = c.execute(
            'SELECT MAX(water)'
            ' FROM status s JOIN plant p on s.plant_id = p.id'
            ' WHERE dev_id = ? AND date_tx >= ?', (plant['dev_id'], month_ago,)
        ).fetchone()

        if max_water is None:
            max_water = 1
        else:
            max_water = max_water['MAX(water)']

        results = c.execute(
            'SELECT water, date_tx'
            ' FROM status s JOIN plant p on s.plant_id = p.id'
            ' WHERE dev_id = ?'  # ' AND date_tx >= ?'
            ' ORDER BY date_tx ASC', (plant['dev_id'], day_offset,)).fetchall()
        water[plant['dev_id']] = [dict([('x', (
                datetime.strptime(row['date_tx'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)).strftime(
            '%Y-%m-%d %H:%M:%S')), ('y', round(row['water'] / max_water * 100,2))]) for row in results]
        if len(water[plant['dev_id']]) > 0 and water[plant['dev_id']][-1]['y'] < 20:
            plant['danger_level'] = 1
        else:
            plant['danger_level'] = 0

    return jsonify(water=water, plants=plants)
