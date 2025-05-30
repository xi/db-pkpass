.PHONY: test
test: .venv muster
	.venv/bin/python3 -m unittest

.venv:
	python3 -m venv .venv
	.venv/bin/python3 -m pip install -r requirements.txt

muster:
	mkdir -p muster
	wget 'https://assets.static-bahn.de/dam/jcr:95540b93-5c38-4554-8f00-676214f4ba76/Muster%20918-9.zip'
	cd muster && unzip "../Muster 918-9.zip"
	rm "Muster 918-9.zip"

.PHONY: clean
clean:
	rm -rf venv muster
