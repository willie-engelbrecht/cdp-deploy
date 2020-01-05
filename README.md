# cdp-deploy

cdp-deploy is a bash script that will install a full single node CDP Data Center cluster using Cloudera Manager. The aim is that cdp-deploy will always install the latest version of CDP and Cloudera Manager which is currently available for download from the [Cloudera website](https://www.cloudera.com/downloads.html).<br />
You will require a paywall username/password to download the bits and install. If you have access to CDF and its components, you can also set a flag for cdp-deploy to install those bits as well. 

Latest installation version: CDP DC 7.0.3

### Requirements
cdp-deploy works only on CentOS 7 or RHEL 7. OpenJDK 8 will be used. PostgreSQL 10 will be the underlying database for all the components.

Your system needs at minimum 64GB RAM and at least 100GB disk space. <br />
A good instance type on AWS would be: m5.4xlarge

An Internet connection is also required, as cdp-deploy will download various files required to perform the automated installation.

### Usage
The general gist to use cdp-deploy:
```
yum -y install git
git clone https://github.com/willie-engelbrecht/cdp-deploy.git

# Edit cdp-deploy/repo.env, and add your paywall username/password
export PWALL_USER=""
export PWALL_PASS=""

# Now run the script
./cdp-deploy/cdp-deploy.sh
```

All download bits are behind a customer paywall, and only Cloudera customers have access to the binaries. Non customers can get access by creating a trial account and then you will have access for 60 days. Once you have your paywall username and password, you need to edit the repo.env file and add your username/password. This is required by the script to download the software:
```
export PWALL_USER=""
export PWALL_PASS=""
```

By default cdp-deploy will setup and download repositories directly from the internet. However it is also possible to use hdp-deploy in an "offline" mode, by editing the repo.env file and changing the value to 1 for:
```
LOCALREPO=1
```

### Post installation
When cdp-deploy is finished, it will print the following to screen, as well as save it to /root/cm_install.txt
```
Add the following to your hosts file:
192.168.0.125 cdp-7.0.3-test-0.home.local

You can now browse to: http://cdp-7.0.3-test-0.home.local:7180
username: admin
password: admin
```

### Components
cdp-deploy will fully install the following components:
  * Atlas
  * DAS-Lite
  * HBase
  * HDFS
  * Hive
  * Hue
  * Kafka
  * Ranger
  * SOLR
  * Spark2
  * Sqoop
  * Tez
  * Oozie
  * Yarn
  * Zookeeper

If you enable CDF components, cdp-deploy will also install:
  * Flow Registry
  * NiFi
  * Schema Registry
  * SMM
