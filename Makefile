PACKAGE=rssdldmng
VERSION=`python setup.py --version`

.PHONY: ci clean coverage init labels publish style test

all: ci tar

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

release: incbuildno
	git tag $(VERSION)
	git push origin $(VERSION)

incbuildno:
	@sed -ri 's/(PATCH_VERSION = )([0-9]+)(.*)/echo "\1$$((\2+1))\3"/ge' rssdldmng/const.py
	@echo updating version number to: $(VERSION)
	@git commit -am "version $(VERSION)"
	@git push

publish: tar
	python setup.py register
	python setup.py upload
	rm -fr build .egg $(PACKAGE).egg-info

style:
	flake8 --max-line-length=140 $(PACKAGE)

test: clean
	py.test -s --verbose -p no:cacheprovider tests

tar:
	python setup.py sdist bdist_wheel

uninstall:
	pip uninstall -y $(PACKAGE) || true

install: ci uninstall tar
	pip install ./dist/$(PACKAGE)-$(VERSION).tar.gz
