from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for, abort
)
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, UserMixin, LoginManager
from urllib import parse

bp = Blueprint('auth', __name__, url_prefix='/auth')
login_manager = LoginManager()
login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        password = request.form['password']
        password_hash = 'pbkdf2:sha256:50000$8UBKrht6$5adc722aacf305c9dd4eed3a2300a1cf56012ab65b890a08f26b63544abb7e18'

        error = None

        if not check_password_hash(password_hash, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            user = User(0)
            login_user(user)
            flash('Logged in successfully.')
            next_page = request.args.get('next')
            if not is_safe_url(next_page):
                return abort(400)
            return redirect(next_page or url_for('index'))

        flash(error)

    return render_template('auth/login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.')
    return redirect(url_for('index'))


def is_safe_url(target):
    ref_url = parse.urlparse(request.host_url)
    test_url = parse.urlparse(parse.urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


class User(UserMixin):
    def __init__(self, id):
        self.id = id
