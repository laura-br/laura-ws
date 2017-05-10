"""REST Web Service configuration file.

Common configuration between environments.
"""

DEBUG = False
TESTING = False
PORT = 8080
LOCALE = 'pt-br'
CORS_ORIGINS = {'origins': ['https://laurabotintegrationtest.mybluemix.net',
                            'https://laurabotintegration.mybluemix.net']
                }
SQLALCHEMY_DATABASE_URI = ''
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQL_DATE_FORMAT = '%d/%m/%Y %H:%M:%S'
USERNAME = ''
PASSWORD = ''
MAIL_SERVER = 'example.com'
MAIL_PORT = 000
MAIL_USE_SSL = True
MAIL_USERNAME = 'example@example.com'
MAIL_PASSWORD = 'password'
MAIL_DEFAULT_SENDER = '"Web Server" <example@example.com>'
# MAIL_LOG_SENDER = '"Web Server Error Log" <example@example.com>'
ADMINS = ['Someone <example@example.com>']