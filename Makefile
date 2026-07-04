SHELL := /bin/bash

TARGET ?= green
ROLLBACK ?= blue
LOAD_URL ?= http://localhost:8080/api/catalog
LOAD_DURATION ?= 60s
LOAD_RATE ?= 100
ANSIBLE_PLAYBOOK ?= ./scripts/ansible_playbook.sh

.PHONY: up down build smoke verify deploy-green deploy-blue deploy rollback-blue rollback load-test logs ps clean

up:
	./scripts/bootstrap.sh

build:
	docker compose build

down:
	docker compose down

smoke:
	./scripts/smoke_test.sh

verify:
	$(ANSIBLE_PLAYBOOK) ansible/playbooks/verify.yml

deploy:
	$(ANSIBLE_PLAYBOOK) ansible/playbooks/deploy-blue-green.yml -e target_color=$(TARGET)

deploy-green:
	$(ANSIBLE_PLAYBOOK) ansible/playbooks/deploy-blue-green.yml -e target_color=green

deploy-blue:
	$(ANSIBLE_PLAYBOOK) ansible/playbooks/deploy-blue-green.yml -e target_color=blue

rollback:
	$(ANSIBLE_PLAYBOOK) ansible/playbooks/rollback.yml -e rollback_color=$(ROLLBACK)

rollback-blue:
	$(ANSIBLE_PLAYBOOK) ansible/playbooks/rollback.yml -e rollback_color=blue

load-test:
	./scripts/run_load_test.sh $(LOAD_URL) $(LOAD_DURATION) $(LOAD_RATE)

logs:
	docker compose logs -f --tail=120

ps:
	docker compose ps

clean:
	docker compose down --remove-orphans
