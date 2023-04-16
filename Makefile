all: build

.PHONY: build 
build:
	python3 setup.py sdist bdist_wheel

.PHONY: test
test:
	@python3 ./test/crypto_test.py
	@python3 ./test/colonies_test.py

.PHONY: install
install:
	pip3 install dist/pycolonies-0.0.1-py3-none-any.whl

publish:
	python3 -m twine upload dist/*
