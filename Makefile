all: build

.PHONY: build 
build:
	python3 setup.py sdist bdist_wheel

.PHONY: test
test:
	@python3 ./test/crypto_test.py
	@python3 ./test/colonies_test.py

.PHONY: github_test
github_test:
	wget https://github.com/colonyos/colonies/releases/download/v1.0.3/colonies_1.0.3_linux_amd64.tar.gz
	tar -xzf colonies_1.0.3_linux_amd64.tar.gz
	cp ./colonies_1.0.3_linux_amd64/colonies .
	@./colonies keychain add --id $COLONIES_COLONY_ID --prvkey $COLONIES_COLONY_PRVKEY
	@./colonies keychain add --id $COLONIES_EXECUTOR_ID --prvkey $COLONIES_EXECUTOR_PRVKEY
	@./colonies keychain add --id $BEMIS_SERVER_EXECUTOR_ID --prvkey $BEMIS_SERVER_EXECUTOR_PRVKEY
	@./colonies colony add --spec ./colony.json --colonyprvkey $COLONIES_COLONY_PRVKEY
	@./colonies executor add --spec ./cli_executor.json --executorprvkey $COLONIES_EXECUTOR_PRVKEY
	@./colonies executor approve --executorid $COLONIES_EXECUTOR_ID
	@pip3 install -r requirements.txt
	@python3 ./test/crypto_test.py
	@python3 ./test/colonies_test.py

.PHONY: install
install:
	pip3 install dist/pycolonies-0.0.1-py3-none-any.whl

publish:
	python3 -m twine upload dist/*
