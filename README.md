# RSS Download Manager


## Description

Parses rss feeds from showrss.info, adds magnet links to transmission, and when download finishes, updates kodi database
Provides restAPI to access local DB, config, status
Can get TV show list from Trakt list


## Usage (installing from web inside docker)

build docker image from github
```
docker build --no-cache --pull --rm -t alexpayne/rssdldmng:latest https://github.com/alexpayne482/rssdldmng.git#:docker
```

build docker image from local repo
```
python setup.py sdist bdist_wheel
cp ./dist/$(ls -tR ./dist | grep .tar.gz | head -n 1) ./docker/rssdldmng.tar.gz
docker build --no-cache --pull --rm -t alexpayne/rssdldmng:latest ./docker
```

save docker image
```
docker save -o docker_rssdldmng.tar alexpayne/rssdldmng
```

run docker image
```
docker run \
        -e PUID=$UID \
        -e PGID=$(id -g) \
        -p 9091:9091 \
        -p 8090:8090 \
        -v <path to data>:/config \
        -v <path to downloads>:/downloads \
        -v <path to watch folder>:/watch \
        alexpayne/rssdldmng:latest
```

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
wget https://github.com/$(curl -sL https://github.com/alexpayne482/rssdldmng/releases/latest | grep -i "/rssdldmng-.*.tar.gz" | cut -d '"' -f 2)
pip install $(ls -tR . | grep "rssdldmng-.*.tar.gz" | head -n 1)
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

Trakt.tv login before starting the service:
Follow on screen instrunctions (login data will be stored in $HOME/.pytrakt.json)
Must be done every 90 days.
```
python -c "import trakt; trakt.init(store=True)"
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

run style checks and tests, build package
```
make all
```

install latest build
```
make install
```
