from flask import (
    Blueprint, flash, render_template, request, current_app
)

from BigBrewer.db import get_db
from flask_login import current_user

bp = Blueprint('info', __name__)


@bp.route('/')
def index():
    return render_template('info/index.html')


@bp.route('/monitor')
def monitor():
    return render_template('info/monitor.html')


# @bp.route('/plants', methods=['GET', 'POST'])
# def plants():
#     db = get_db()
#     if request.method == 'POST':
#         if request.form['action'] == 'delete':
#             if current_user.is_authenticated:
#                 dev_id = request.form['dev_id']
#                 error = None

#                 if not dev_id:
#                     error = 'Something went wrong.'
#                 elif db.execute(
#                         'SELECT id FROM plant WHERE dev_id = ?', (dev_id,)
#                 ).fetchone() is None:
#                     error = 'Device {} does not exist, something went wrong.'.format(dev_id)

#                 if error is None:
#                     db.execute(
#                         'DELETE FROM plant WHERE dev_id = ?',
#                         (dev_id,)
#                     )
#                     db.commit()
#                 else:
#                     flash(error)
#                     current_app.logger.warning(error)
#             else:
#                 flash('You need to log in to perform this action')

#         elif request.form['action'] == 'reset':
#             if current_user.is_authenticated:
#                 dev_id = request.form['dev_id']
#                 error = None

#                 if not dev_id:
#                     error = 'Something went wrong.'
#                 result = db.execute('SELECT id FROM plant WHERE dev_id = ?', (dev_id,)).fetchone()
#                 if result is None:
#                     error = 'Device {} does not exist, something went wrong.'.format(dev_id)

#                 if error is None:
#                     db.execute(
#                         'DELETE FROM status WHERE plant_id = ?',
#                         (result['id'],)
#                     )
#                     db.commit()
#                 else:
#                     flash(error)
#                     current_app.logger.warning(error)
#             else:
#                 flash('You need to log in to perform this action')

#     plants = db.execute(
#         'SELECT id, plantname, dev_id, color, location'
#         ' FROM plant'
#         ' ORDER BY plantname DESC'
#         # 'SELECT plantname, dev_id, color, location, voltage, date_tx'
#         # ' FROM plant JOIN status on status.id = ('
#         # ' SELECT id FROM status'
#         # ' WHERE status.plant_id = plant.id'
#         # ' ORDER BY date_tx DESC'
#         # ' LIMIT 1)'
#         # ' ORDER BY plantname ASC'
#     ).fetchall()
#     voltages = dict()
#     for plant in plants:
#         result = db.execute(
#             'SELECT voltage'
#             ' FROM status s JOIN plant p on s.plant_id = p.id'
#             ' WHERE plant_id = ?'
#             ' ORDER BY date_tx ASC', (plant['id'],)).fetchone()
#         if result is None:
#             voltages[plant['dev_id']] = 0
#         else:
#             voltages[plant['dev_id']] = result['voltage']

#     return render_template('info/plants.html', plants=plants, voltages=voltages)
