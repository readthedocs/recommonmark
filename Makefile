CWD := $(shell pwd)
ARGS := ""

.PHONY: all
all: clean

.PHONY: install
install: env
env:
	@virtualenv env
	@env/bin/python3 ./setup.py install

.PHONY: uninstall
uninstall:
	-@rm -rf env >/dev/null || true

.PHONY: reinstall
reinstall: uninstall install

.PHONY: freeze
freeze:
	@env/bin/pip3 freeze

.PHONY: build
build: dist
dist: clean install
	@env/bin/python3 setup.py sdist
	@env/bin/python3 setup.py bdist_wheel

.PHONY: publish
publish: dist
	@twine upload dist/*
	@echo published

.PHONY: test
test: install
test:
	@env/bin/python3 -m unittest discover tests

.PHONY: link
link: install
	@pip3 install -e .

.PHONY: unlink
unlink: install
	@rm -r $(shell find . -name '*.egg-info')

.PHONY: clean
clean:
	@git clean -fXd -e !/env -e !/env/**/*
