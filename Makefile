.PHONY: worker beat server shell migrate

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
