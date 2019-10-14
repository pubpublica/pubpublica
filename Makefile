.ONESHELL:

venv=venv
PYTHONPATH=.
PYTHON=${venv}/bin/python

serve:
	uwsgi --ini pubpublica.ini

debug:
	. venv/bin/activate
	PYTHONPATH=${PYTHONPATH} FLASK_ENV=development FLASK_DEBUG=1 ${PYTHON} wsgi.py

test:
	. venv/bin/activate
	PYTHONPATH=${PYTHONPATH} pytest

check:
	. venv/bin/activate
	PYTHONPATH=${PYTHONPATH} ${PYTHON} tools/check_links.py "publications/"

status:
	. venv/bin/activate
	PYTHONPATH=${PYTHONPATH} ${PYTHON} tools/status.py $(host)

provision:
	. venv/bin/activate
	PYTHONPATH=${PYTHONPATH} ${PYTHON} tools/provision.py $(host)

deploy:
	. venv/bin/activate
	PYTHONPATH=${PYTHONPATH} ${PYTHON} tools/deploy.py $(host)
