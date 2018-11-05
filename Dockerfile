FROM centos:7

LABEL maintainer "Mats Rynge <rynge@isi.edu>"

RUN yum -y upgrade
RUN yum -y install epel-release yum-plugin-priorities

# osg repo
RUN yum -y install http://repo.opensciencegrid.org/osg/3.4/osg-3.4-el7-release-latest.rpm

# pegasus repo
RUN echo -e "# Pegasus\n[Pegasus]\nname=Pegasus\nbaseurl=http://download.pegasus.isi.edu/wms/download/rhel/7/\$basearch/\ngpgcheck=0\nenabled=1\npriority=50" >/etc/yum.repos.d/pegasus.repo

RUN yum -y install \
    astropy-tools \
    file \
    gcc \
    gcc-gfortran \
    java-1.8.0-openjdk \
    java-1.8.0-openjdk-devel \
    libjpeg-turbo-devel \
    openjpeg-devel \
    osg-ca-certs \
    osg-wn-client \
    pegasus \
    python-astropy \
    python-devel \
    python-future \
    python-pip \
    unzip \
    wget

# Cleaning caches to reduce size of image
RUN yum clean all

# wget -nv http://montage.ipac.caltech.edu/download/Montage_v5.0.tar.gz 
RUN cd /opt && \
    wget -nv https://github.com/Caltech-IPAC/Montage/archive/master.zip && \
    unzip master.zip && \
    rm -f master.zip && \
    mv Montage-master Montage && \
    cd Montage && \
    make

RUN mkdir /opt/montage-workflow-v2

ADD * /opt/montage-workflow-v2/


