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
	wget https://github.com/colonyos/colonies/releases/download/v1.8.7/colonies_1.8.7_linux_amd64.tar.gz
	tar -xzf colonies_1.8.7_linux_amd64.tar.gz
	env
	./colonies database create
	./colonies colony add --name ${COLONIES_COLONY_NAME} --colonyid ${COLONIES_COLONY_ID} 
	./colonies executor add --spec ./executor.json --executorid ${COLONIES_EXECUTOR_ID}
	./colonies executor approve --name ${COLONIES_EXECUTOR_NAME}
	@pip3 install -r requirements.txt
	@python3 ./test/crypto_test.py
	@python3 ./test/colonies_test.py

.PHONY: install
install:
	pip3 install dist/pycolonies-1.0.24-py3-none-any.whl --force-reinstall 

publish:
	python3 -m twine upload dist/pycolonies-1.0.24-py3-none-any.whl 
