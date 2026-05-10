.PHONY: worker beat server shell migrate seed

worker:
	python3 -m celery -A config worker --loglevel=info

beat:
	python3 -m celery -A config beat --loglevel=info

server:
	python3 manage.py runserver

shell:
	python3 manage.py shell

migrate:
	python3 manage.py migrate
make-migration:
	python3 manage.py makemigrations

collect:
	python3 manage.py collectstatic --no-input
require:
	pip install -r requirements.txt

seed:
	python3 manage.py seed_tools
	python3 manage.py generate_seo_pages
