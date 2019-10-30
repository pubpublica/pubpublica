PYTHONPATH := "."
VENV := venv
BIN := ${VENV}/bin
PYTHON := ${BIN}/python3.8
PIP := ${BIN}/pip3.8

test:
	PYTHONPATH=${PYTHONPATH} pytest

install:
	python3.8 -m venv venv
	${PIP} install --upgrade pip
	${PIP} install -r requirements.in

debug:
	PYTHONPATH=${PYTHONPATH} FLASK_ENV=development FLASK_DEBUG=1 ${PYTHON} wsgi.py

gunicorn:
	${BIN}/gunicorn "wsgi:application" --config gunicorn.py

uwsgi:
	${BIN}/uwsgi --ini uwsgi.ini
