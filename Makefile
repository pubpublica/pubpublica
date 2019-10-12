serve:
	uwsgi --ini wsgi.ini

check:
	python pubpublica/check_links.py pubpublica/publications/

test:
	pytest
