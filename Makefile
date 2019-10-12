serve:
	uwsgi --ini pubpublica.ini

debug:
	python wsgi.py

check:
	python pubpublica/check_links.py pubpublica/publications/

test:
	pytest
