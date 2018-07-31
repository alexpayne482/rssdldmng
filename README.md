# RSS Download Manager


## Description

Parses rss feeds from showrss.info, adds magnet links to transmission, and when download finishes, updates kodi database
Provides restAPI to access local DB, config, status and alter shows list


## Usage (installing from web)

install package with pip (not yet published, so does not work)
```
pip install rssdldmng
```

install package with pip from archive
```
wget ....
pip install rssdldmng-0.2.0.dev0.tar.gz
```

run
```
rssdldmng
```

make service with autostart
```
wget ....
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
