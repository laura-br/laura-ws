from flask import Flask
from flask import request
from flask import Response
from flask import jsonify
from flask_mail import Mail
from flask_mail import Message
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
from smtplib import SMTPException
import os
from json import dumps, load
from datetime import date
from datetime import datetime


app = Flask(__name__)


# Load app configuration
app.config.from_object('config')

# Put in a easy to type variable
conf = app.config

# Get the port number from the environment variable PORT
# Default the port to the config PORT
port = int(os.getenv('PORT', conf['PORT']))

# Load Flask E-mail Module
mail = Mail(app)

# Connect to the database
db = SQLAlchemy(app)


def send_mail(subject, message):
    """Send a notification mail to ADMINS."""

    subject = "[WEB_SERVICE] {}".format(subject)
    message = ("Hi.\n\n" +
               "Something happend on the Web Service.\n" +
               "This message should help you find out what happend:\n" +
               message)

    msg = Message(recipients=conf['ADMINS'],
                  subject=subject,
                  body=message)
    try:
        mail.send(msg)
    except SMTPException as e:
        app.logger.error("Error sending message: {}".format(e))
        return -1
    return 0


# Load views config
if os.path.isfile('views_config.json'):
    with open('views_config.json') as data_file:
        views_conf = load(data_file)
else:
    print('No configuration file')
    subject = "Views configurations not found"
    message = "The views configurations file doesn't exist and it must be"
    "created."
    send_mail(subject, message)
    exit(1)


def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, date):
        return obj.isoformat()


def check_existing_view(f):
    """Create this view function to be wraped in a decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if (kwargs['view'] not in views_conf):
            return Response('View {} not found.\n'.format(kwargs['view']), 400)
        return f(*args, **kwargs)
    return decorated


def check_auth(username, password):
    """Check if a username / password combination is valid."""
    return (username == conf['USERNAME'] and
            password == conf['PASSWORD'])


def authenticate():
    """Send a 401 response that enables basic auth."""
    return Response('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    """Create this view function to be wraped in a decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            if not check_auth(request.args.get('user'),
                              request.args.get('pass')):
                return authenticate()
        return f(*args, **kwargs)
    return decorated


def validate(date_text):
    """Validate if the parameter text is a date."""
    try:
        datetime.strptime(date_text.strip('\''), '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return False
    return True


def get_date_in_format(date_text):
    date = datetime.strptime(date_text.strip('\''), '%Y-%m-%d %H:%M:%S')
    return datetime.strftime(date, conf['SQL_DATE_FORMAT'])


def check_params(f):
    """Create this view function to be wraped in a decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        missing_parameters = []
        for param in views_conf[kwargs['view']]['parameters']:
            if not request.args.get(param):
                missing_parameters.append(param)
                continue

            if not validate(request.args.get(param)):
                return Response('Parameters must be a date in the format '
                                'yyyy-mm-dd hh:mm:ss.\n', 400)

        if missing_parameters:
            return Response(
                'Missing parameters.\n{}'.format(missing_parameters), 400)

        return f(*args, **kwargs)
    return decorated


def get_params(parameters):
    params = []
    for param in parameters:
        if (request.args.get(param)):
            date_str = get_date_in_format(request.args.get(param))
            params.append("'{}'".format(date_str))
    return params


@app.route('/<view>', methods=['GET'])
@check_existing_view
@requires_auth
@check_params
def get_view(view):
    """Return the result of the query using the parameters."""
    if db:
        fixed_params = get_params(views_conf[view]['parameters'])
        fixed_query = views_conf[view]['query'].format(parameters=fixed_params)
        optional_params = []
        if 'optional_parameters' in views_conf[view]:
            optional_params = get_params(
                views_conf[view]['optional_parameters'])
        optional_query = ""
        if 'optional_query' in views_conf[view] and optional_params:
            optional_query = views_conf[view]['optional_query'].format(
                optionals=optional_params)
        query = "{} {}".format(fixed_query, optional_query)
        result = db.engine.execute(query)
        return dumps([dict(r) for r in result], default=alchemyencoder)
    else:
        print('No database')
        subject = "Database not found error"
        message = "The database variable is None and it shouldn't be."
        send_mail(subject, message)
        return jsonify([])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=conf['DEBUG'],
            use_reloader=conf['DEBUG'], threaded=True)
