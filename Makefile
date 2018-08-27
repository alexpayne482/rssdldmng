PACKAGE=rssdldmng

.PHONY: ci clean coverage init labels publish style test

ci: init style test

clean:
	rm -rf $(PACKAGE)/*.pyc
	rm -rf $(PACKAGE)/__pycache__
	rm -rf $(PACKAGE)/__pycache__
	rm -rf $(PACKAGE).egg-info

#coverage:
#	py.test --verbose --cov-report term-missing --cov=$(PACKAGE) -p no:cacheprovider tests


init:
	pip install -r testing-requirements.txt

labels:
	ghlabels -remove -file .github/labels.json

publish: tar
	python setup.py register
	python setup.py upload
	rm -fr build dist .egg $(PACKAGE).egg-info

style:
	flake8 --max-line-length=140 $(PACKAGE)

test: clean
	py.test -s --verbose -p no:cacheprovider tests

tar:
	python setup.py sdist bdist_wheel

uninstall:
	pip uninstall -y $(PACKAGE) || true

install: uninstall tar
	pip install ./dist/$(shell ls -tR . | grep .tar.gz | head -n 1)