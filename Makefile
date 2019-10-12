serve:
	uwsgi --ini wsgi.ini

debug:
	python wsgi.py

check:
	python pubpublica/check_links.py pubpublica/publications/

test:
	pytest
