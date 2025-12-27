all: build

.PHONY: build
build:
	python3 setup.py sdist bdist_wheel

.PHONY: test
test:
	@python3 ./test/crypto_test.py
	@python3 ./test/colonies_test.py
	@python3 ./test/channel_test.py
	@python3 ./test/blueprint_test.py
	@python3 ./test/api_test.py

.PHONY: setup
setup:
	@pip3 install -r requirements.txt
	@python3 ./test/setup_test_env.py

.PHONY: github_test
github_test:
	@pip3 install -r requirements.txt
	@python3 ./test/setup_test_env.py
	@python3 ./test/crypto_test.py
	@python3 ./test/colonies_test.py
	@python3 ./test/channel_test.py
	@python3 ./test/blueprint_test.py
	@python3 ./test/api_test.py

.PHONY: install
install:
	pip3 install dist/pycolonies-1.0.25-py3-none-any.whl --force-reinstall

.PHONY: publish
publish:
	python3 -m twine upload dist/pycolonies-1.0.25-py3-none-any.whl

.PHONY: clean
clean:
	rm -rf build dist *.egg-info __pycache__ .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete
