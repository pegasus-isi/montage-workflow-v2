bootstrap:docker
From:debian:9

%setup

mkdir $SINGULARITY_ROOTFS/opt/montage-workflow-v2
cp -a * $SINGULARITY_ROOTFS/opt/montage-workflow-v2/


%post

apt-get update && apt-get install -y \
        build-essential \
        curl \
        gfortran \
        gnupg \
        libmariadbclient18 \
        libpq5 \
        openjdk-8-jre \
        pkg-config \
        python \
        python-astropy \
        python-dev \
        python-pip \
        unzip \
        vim \
        wget
        
# pegasus
#wget -O - http://download.pegasus.isi.edu/pegasus/gpg.txt | apt-key add -
#echo 'deb http://download.pegasus.isi.edu/wms/download/debian stretch main' >/etc/apt/sources.list.d/pegasus.list
#apt-get update && apt-get install -y \
#    pegasus
wget http://download.pegasus.isi.edu/pegasus/4.8.0dev/pegasus_4.8.0dev-1+deb9_amd64.deb
dpkg -i pegasus_4.8.0dev-1+deb9_amd64.deb

apt-get clean
rm -rf /var/lib/apt/lists/*

cd /opt && \
    wget -nv http://montage.ipac.caltech.edu/download/Montage_v5.0.tar.gz && \
    tar xzf Montage_v5.0.tar.gz && \
    rm -f Montage_v5.0.tar.gz && \
    cd Montage && \
    make

