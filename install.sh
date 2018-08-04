#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
CWD=$(pwd)
cd $DIR

# build pip package
python setup.py sdist bdist_wheel

# install pip package
pip uninstall -y rssdldmng
pip install ./dist/$(ls -tR . | grep .tar.gz | head -n 1)

cd $CWD

# install as a service
$DIR/make_service.sh
