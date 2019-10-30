venv := "venv"
PYTHONPATH := "."
PYTHON := venv + "/bin/python"

test:
	. venv/bin/activate
	PYTHONPATH={{PYTHONPATH}} pytest

debug:
	. venv/bin/activate
	PYTHONPATH={{PYTHONPATH}} FLASK_ENV=development FLASK_DEBUG=1 {{PYTHON}} wsgi.py

gunicorn:
	gunicorn 'wsgi:application' --config gunicorn.py

uwsgi:
	uwsgi --ini uwsgi.ini
