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
        session_id = None
        if sensor_id is None:
            error = 'Device {} is not yet registered.'.format(dev_id)
        else:
            print("sersor ID:", sensor_id[0])
            session_id = db.execute(
                'SELECT id FROM session WHERE sensor_id = ? ORDER BY begin_time DESC',
                (sensor_id[0],)
            ).fetchone()
            if session_id is None:
                error = 'Device {} is not yet used by any session.'.format(dev_id)

        if error is None:
            db.execute(
                'INSERT INTO status(sensor_id, session_id, temperature, voltage, date_tx)'
                ' VALUES(?, ?, ?, ?, ?)',
                (sensor_id[0], session_id[0], temperature, voltage, date)
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


@bp.route('/createsession', methods=['GET', 'POST'])
def createsession():
    if request.method == 'POST':
        print("CREATING NEW SESSION!")
        print(request.form)
        sessionname = request.form['session_name']
        print(sessionname)
        dev_id = request.form['session_sensor']
        print(dev_id)
        type = request.form['session_type']
        print(type)
        color = request.form['color']
        print(color)
        db = get_db()
        error = None

        if not sessionname:
            error = 'Session name is required.'
        elif not dev_id:
            error = 'Attatched sensor is required.'
        elif not type:
            error = 'Define the type of the session.'

        sensor_id = db.execute(
            'SELECT id FROM sensor WHERE dev_id = ?', (dev_id,)
        ).fetchone()[0]

        # print("sensor ID", sensor_id)

        current_session = db.execute(
            'SELECT id FROM session WHERE sensor_id = ?'
            'ORDER BY begin_time DESC', (sensor_id,)
        ).fetchone()

        if current_session is not None:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print("Current session:", current_session[0])
            print("Current timestamp", timestamp)
            # type_new = 'test'
            print("Stopping other session that used the same sensor")
            db.execute(
                'UPDATE session SET end_time = ? WHERE id = ?',
                (timestamp, current_session[0],)
            )

        if error is None:
            db.execute(
                'INSERT INTO session (session_name, type, color, sensor_id) \
                VALUES (?, ?, ?, ?)', (sessionname, type, color, sensor_id)
            )
            db.commit()
            return redirect(url_for('info.index'))

        flash(error)
        current_app.logger.warning(error)
    if request.method == 'GET':
        db = get_db()
        sensors = db.execute(
                'SELECT dev_id'
                ' FROM sensor'
                ' ORDER BY dev_id DESC'
                ).fetchall()
    return render_template('temperature/session.html', sensors=sensors)


# @bp.route('/data', defaults={'session' : None}, methods=['GET'])
@bp.route('/data', methods=['GET'])
def get_data():
    db = get_db()
    c = db.cursor()
    sessions = c.execute(
        'SELECT id, session_name'
        ' FROM session'
        ' ORDER BY id DESC'
    ).fetchall()
    sessions = [dict(zip([key[0] for key in c.description], row)) for row in sessions]

    today = date.today()
    last_n_days = 7
    day_offset = today - timedelta(days=last_n_days)
    # month_ago = today - timedelta(days=31)
    temperature = dict()
    for session in sessions:
        # max_temperature = c.execute(
        #     'SELECT MAX(temperature)'
        #     ' FROM status s JOIN sensor p on s.sensor_id = p.id'
        #     ' WHERE dev_id = ? AND date_tx >= ?', (sensor['dev_id'], month_ago,)
        # ).fetchone()

        # if max_temperature is None:
        #     max_temperature = 1
        # else:
        #     max_temperature = max_temperature['MAX(temperature)']

        results = c.execute(
            'SELECT temperature, date_tx'
            ' FROM status s JOIN session p on s.session_id = p.id'
            ' WHERE session_id = ? AND date_tx >= ?'
            ' ORDER BY date_tx ASC', (session['id'], day_offset, )).fetchall()
        # print(results)
        temperature[session['id']] = [dict([('x', (
                datetime.strptime(row['date_tx'], '%Y-%m-%d %H:%M:%S') + timedelta(hours=1)).strftime(
            '%Y-%m-%d %H:%M:%S')), ('y', row['temperature'])]) for row in results]

    return jsonify(temperature=temperature, sessions=sessions)


@bp.route('/current_temperature', methods=['GET'])
def current_temperature():
    db = get_db()
    c = db.cursor()
    sessions = c.execute(
        'SELECT id, session_name'
        ' FROM session'
        ' ORDER BY id DESC'
    ).fetchall()
    sessions = [dict(zip([key[0] for key in c.description], row)) for row in sessions]

    # print('GETTING CURRENT TEMP')
    current_temp = dict()
    for session in sessions:
        temp = c.execute(
            'SELECT temperature '
            'FROM status s JOIN session p on s.session_id = p.id'
            ' WHERE session_id = ?'
            ' ORDER BY date_tx DESC', (session['id'], )).fetchone()
        current_temp[session['id']] = temp[0]
    return jsonify(current_temp=current_temp)
