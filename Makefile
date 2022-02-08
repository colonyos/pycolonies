all: build

build:
	python3 -m build

.PHONY: test
test:
	@python3 ./test/crypto_test.py
	@python3 ./test/colonies_test.py
