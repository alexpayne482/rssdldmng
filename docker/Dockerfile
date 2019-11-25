FROM lsiobase/alpine:3.10

# set version label
ARG BUILD_DATE
ARG VERSION
LABEL build_version="rssdldmng version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="alexpayne"

RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories

RUN \
 echo "**** install packages ****" && \
 apk add --no-cache \
	curl \
	findutils \
	jq \
	openssl \
	p7zip \
	python \
	py3-setuptools \
	py-pip \
	rsync \
	tar \
	transmission-cli \
	transmission-daemon \
	unrar \
	unzip \
	sqlite \
	sqlite-dev && \
 echo "**** install third party themes ****" && \
 curl -o \
	/tmp/combustion.zip -L \
	"https://github.com/Secretmapper/combustion/archive/release.zip" && \
 unzip \
	/tmp/combustion.zip -d \
	/ && \
 mkdir -p /tmp/twctemp && \
 TWCVERSION=$(curl -sX GET "https://api.github.com/repos/ronggang/transmission-web-control/releases/latest" | awk '/tag_name/{print $4;exit}' FS='[""]') && \
 curl -o \
	/tmp/twc.tar.gz -L \
	"https://github.com/ronggang/transmission-web-control/archive/${TWCVERSION}.tar.gz" && \
 tar xf \
	/tmp/twc.tar.gz -C \
	/tmp/twctemp --strip-components=1 && \
 mv /tmp/twctemp/src /transmission-web-control && \
 mkdir -p /kettu && \
 curl -o \
	/tmp/kettu.tar.gz -L \
	"https://github.com/endor/kettu/archive/master.tar.gz" && \
 tar xf \
	/tmp/kettu.tar.gz -C \
	/kettu --strip-components=1 && \
 RSSDLDMNGVERSION=$(curl -sX GET "https://api.github.com/repos/alexpayne482/rssdldmng/releases/latest" | awk '/tag_name/{print $4;exit}' FS='[""]') && \
 curl -o \
	/tmp/rssdldmng.tar.gz -L \
	"https://github.com/alexpayne482/rssdldmng/releases/download/${RSSDLDMNGVERSION}/rssdldmng-${RSSDLDMNGVERSION}.tar.gz" && \
 pip3 install /tmp/rssdldmng.tar.gz && \
 echo "**** cleanup ****" && \
 rm -rf \
	/tmp/*


# copy local files
COPY root/ /

# ports and volumes
EXPOSE 9091 51413
VOLUME /config /downloads /watch
