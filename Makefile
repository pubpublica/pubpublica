serve:
	uwsgi --ini pubpublica.ini

debug:
	FLASK_DEBUG=1 python wsgi.py

check:
	python pubpublica/check_links.py pubpublica/publications/

test:
	pytest
