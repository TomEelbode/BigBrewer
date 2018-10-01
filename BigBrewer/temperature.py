import pandas as pd
from flask import current_app, jsonify
from datetime import datetime, date, timedelta

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for
)

from BigBrewer.db import get_db

bp = Blueprint('temperature', __name__, url_prefix='/temperature')


# curl --header "Content-Type: application/json" --request POST --data '{"metadata": {"time": "2018-05-29T11:25:11.875464918Z"}, "app_id": "bigbrewer", "dev_id": "tempsen1", "payload_fields": {"voltage": 26.214, "temperature": 6710886}}' 192.168.0.174:5000/ttn/submit

@bp.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        current_app.logger.info(request.get_json())
        data = request.get_json()
        # print(data)
        metadata = data["metadata"]
        date = pd.to_datetime(metadata['time']).strftime('%Y-%m-%d %H:%M:%S')

        dev_id = data['dev_id']

        payload = data['payload_fields']
        temperature = payload['temperature']
        # print(temperature)
        voltage = payload['voltage']
        db = get_db()
        error = None
        if not temperature:
            error = 'Temperature is required.'
        elif not voltage:
            error = 'Voltage is required.'

        sensor_id = db.execute(
            'SELECT id FROM sensor WHERE dev_id = ?', (dev_id,)
        ).fetchone()
        if sensor_id is None:
            error = 'Device {} is not yet registered.'.format(dev_id)

        if error is None:
            db.execute(
                'INSERT INTO status(sensor_id, temperature, voltage, date_tx) \
                VALUES(?, ?, ?, ?)',
                (sensor_id[0], temperature, voltage, date)
            )
            db.commit()
        else:
            current_app.logger.warning(error)

    return request.query_string


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        sensorname = request.form['sensorname']
        dev_id = request.form['dev_id']
        db = get_db()
        error = None

        if not sensorname:
            error = 'Sensorname is required.'
        elif not dev_id:
            error = 'Device_id is required.'
        elif db.execute(
                'SELECT id FROM sensor WHERE dev_id = ?', (dev_id,)
        ).fetchone() is not None:
            error = 'Device {} already exists.'.format(dev_id)

        if error is None:
            db.execute(
                'INSERT INTO sensor (dev_id, sensorname) VALUES (?, ?)',
                (dev_id, sensorname)
            )
            db.commit()
            return redirect(url_for('info.index'))

        flash(error)
        current_app.logger.warning(error)

    return render_template('temperature/register.html')


@bp.route('/data', methods=['GET'])
def get_data():
    db = get_db()
    c = db.cursor()
    sensors = c.execute(
        'SELECT sensorname, dev_id'
        ' FROM sensor'
    ).fetchall()
    sensors = [dict(zip([key[0] for key in c.description], row)) for row in sensors]

    today = date.today()
    last_n_days = 7
    day_offset = today - timedelta(days=last_n_days)
    month_ago = today - timedelta(days=31)
    temperature = dict()
    for sensor in sensors:
        max_temperature = c.execute(
            'SELECT MAX(temperature)'
            ' FROM status s JOIN sensor p on s.sensor_id = p.id'
            ' WHERE dev_id = ? AND date_tx >= ?', (sensor['dev_id'], month_ago,)
        ).fetchone()

        if max_temperature is None:
            max_temperature = 1
        else:
            max_temperature = max_temperature['MAX(temperature)']

        results = c.execute(
            'SELECT temperature, date_tx'
            ' FROM status s JOIN sensor p on s.sensor_id = p.id'
            ' WHERE dev_id = ?'
            ' ORDER BY date_tx ASC', (sensor['dev_id'],)).fetchall()
        # print(results)
        temperature[sensor['dev_id']] = [dict([('x', (
                datetime.strptime(row['date_tx'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=2)).strftime(
            '%Y-%m-%d %H:%M:%S')), ('y', row['temperature'])]) for row in results]

    return jsonify(temperature=temperature, sensors=sensors)
