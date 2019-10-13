serve:
	uwsgi --ini pubpublica.ini

debug:
	FLASK_ENV=development FLASK_DEBUG=1 python wsgi.py

test:
	pytest

check:
	python tools/check_links.py "pubpublica/publications/"

status:
	python tools/status.py $(host)

provision:
	python tools/provision.py $(host)

deploy:
	python tools/deploy.py $(host)
