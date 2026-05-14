.PHONY: help worker beat server shell migrate make-migration collect require check seed audit \
        health env-summary startup-check deploy-verify

# Local dev always uses local settings
LOCAL_ENV = DJANGO_SETTINGS_MODULE=config.settings.local DJANGO_ENV=local

help:
	@echo "LamGen — common targets"
	@echo "  make server           Django dev server (local)"
	@echo "  make shell            Django shell (local)"
	@echo "  make migrate          apply migrations"
	@echo "  make make-migration   create migrations"
	@echo "  make collect          collectstatic --no-input"
	@echo "  make require          pip install -r requirements.txt"
	@echo "  make check            Django system checks"
	@echo "  make seed             full DB seed"
	@echo "  make audit            python3 scripts/audit.py"
	@echo "  make worker           Celery worker (local)"
	@echo "  make beat             Celery beat (local)"
	@echo "  make health           run health_check command"
	@echo "  make env-summary      print environment summary"
	@echo "  make startup-check    run startup_diagnostics"
	@echo "  make deploy-verify    run deployment_verify"

worker:
	$(LOCAL_ENV) python3 -m celery -A config worker --loglevel=info

beat:
	$(LOCAL_ENV) python3 -m celery -A config beat --loglevel=info

server:
	$(LOCAL_ENV) python3 manage.py runserver

shell:
	$(LOCAL_ENV) python3 manage.py shell

migrate:
	$(LOCAL_ENV) python3 manage.py migrate

make-migration:
	$(LOCAL_ENV) python3 manage.py makemigrations

collect:
	$(LOCAL_ENV) python3 manage.py collectstatic --no-input

require:
	pip install -r requirements.txt

check:
	$(LOCAL_ENV) python3 manage.py check

audit:
	python3 scripts/audit.py

seed:
	$(LOCAL_ENV) python3 manage.py seed_all
	$(LOCAL_ENV) python3 manage.py generate_seo_pages

health:
	$(LOCAL_ENV) python3 manage.py health_check

env-summary:
	$(LOCAL_ENV) python3 manage.py env_summary

startup-check:
	$(LOCAL_ENV) python3 manage.py startup_diagnostics

deploy-verify:
	$(LOCAL_ENV) python3 manage.py deployment_verify
