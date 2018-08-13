# RSS Download Manager


## Description

Parses rss feeds from showrss.info, adds magnet links to transmission, and when download finishes, updates kodi database
Provides restAPI to access local DB, config, status and alter shows list


## Usage (installing from web)

dependencies
```
sudo apt-get install sqlite libsqlite3-dev python3 python3-pip
```

install package with pip (not yet published, so does not work)
```
pip install rssdldmng
```

install package with pip from archive
```
wget https://github.com/alexpayne482/rssdldmng/releases/download/0.4.4/rssdldmng-0.4.4.tar.gz
pip install rssdldmng-0.4.4.tar.gz
```

run
```
rssdldmng
```

default config location
```
~/.rssdldmng/configuration.json
```

make service with autostart
```
wget https://raw.githubusercontent.com/alexpayne482/rssdldmng/master/make_service.sh
./make_service.sh
```

control the service
```
sudo systemctl start rssdldmng
sudo systemctl stop rssdldmng
sudo systemctl restart rssdldmng
sudo journalctl -fu rssdldmng
```


## Usage (building from source)

build pip module:
```
pip install --upgrade setuptools wheel
python setup.py sdist bdist_wheel
```

reinstall local pip module
```
 pip uninstall -y rssdldmng && pip install .
```

install latest release
```
pip install ./dist/$(ls -tR . | grep .tar.gz | head -n 1)
```

do all: build, install package, install as a service and start it
```
./install.sh
```
