#
%define         mongo_home /var/lib/mongo
#
Name:           Percona-Server-MongoDB-34
Version:        @@VERSION@@
Release:        @@RELEASE@@%{?dist}
Summary:        High-performance MongoDB replacement from Percona (metapackage)
Group:          Applications/Databases

License:        SSPL
URL:            https://github.com/percona/percona-server-mongodb.git
Source0:        @@SOURCE_TARBALL@@
Source1:        mongod.conf
Source2:        mongod.service
Source3:        mongod.default
Source4:        percona-server-mongodb-helper.sh
Source5:        mongod.init
Source6:        mongod.pp
Source7:        percona-server-mongodb-enable-auth.sh

BuildRoot:      /var/tmp/%{name}-%{version}-%{release}
%undefine       _missing_build_ids_terminate_build
%define         _unpackaged_files_terminate_build 0

%define         src_dir @@SRC_DIR@@

BuildRequires: gcc, make, cmake, gcc-c++, openssl-devel, cyrus-sasl-devel
BuildRequires: snappy-devel, zlib-devel, libbz2-devel
BuildRequires: libpcap-devel
BuildRequires: /usr/bin/scons

Requires: %{name}-mongos = %{version}-%{release}
Requires: %{name}-server = %{version}-%{release}
Requires: %{name}-shell = %{version}-%{release}
Requires: %{name}-tools = %{version}-%{release}
Requires: numactl libpcap

Conflicts: Percona-Server-MongoDB Percona-Server-MongoDB-32 mongodb-org

%description
This package contains high-performance MongoDB replacement from Percona - Percona Server for MongoDB.
Percona Server for MongoDB is built for scalability, performance and high availability, scaling from single server deployments to large, complex multi-site architectures. By leveraging in-memory computing, Percona Server for MongoDB provides high performance for both reads and writes. Percona Server for MongoDB's native replication and automated failover enable enterprise-grade reliability and operational flexibility.

Percona Server for MongoDB is an open-source database used by companies of all sizes, across all industries and for a wide variety of applications. It is an agile database that allows schemas to change quickly as applications evolve, while still providing the functionality developers expect from traditional databases, such as secondary indexes, a full query language and strict consistency.

Percona Server for MongoDB has a rich client ecosystem including hadoop integration, officially supported drivers for 10 programming languages and environments, as well as 40 drivers supported by the user community.

Percona Server for MongoDB features:
* JSON Data Model with Dynamic Schemas
* Auto-Sharding for Horizontal Scalability
* Built-In Replication for High Availability
* Rich Secondary Indexes, including geospatial
* TTL indexes
* Text Search
* Aggregation Framework & Native MapReduce

This metapackage will install the mongo shell, import/export tools, other client utilities, server software, default configuration, and init.d scripts.

%package mongos
Group:          Applications/Databases
Summary:        Percona Server for MongoDB sharded cluster query router
%description mongos
This package contains mongos - the Percona Server for MongoDB sharded cluster query router
Conflicts: Percona-Server-MongoDB-mongos Percona-Server-MongoDB-32-mongos mongodb-org-mongos

%package server
Group:          Applications/Databases
Summary:        Percona Server for MongoDB database server
Requires: policycoreutils
Requires: %{name}-shell = %{version}-%{release}
%description server
This package contains the Percona Server for MongoDB server software, default configuration files and init.d scripts
Conflicts: Percona-Server-MongoDB-server Percona-Server-MongoDB-32-server mongodb-org-server

%package shell
Group:          Applications/Databases
Summary:        Percona Server for MongoDB shell client
%description shell
This package contains the Percona Server for MongoDB shell
Conflicts: Percona-Server-MongoDB-shell Percona-Server-MongoDB-32-shell mongodb-org-shell

%package tools
Group:          Applications/Databases
Summary:        The tools package for Percona Server for MongoDB
%description tools
This package contains various tools from MongoDB project, recompiled for Percona Server for MongoDB
Conflicts: Percona-Server-MongoDB-tools Percona-Server-MongoDB-32-tools mongodb-org-tools

%debug_package

%prep

%setup -q -n %{src_dir}

%build

export CC=${CC:-gcc}
export CXX=${CXX:-g++}
export PSM_TARGETS="mongod mongos mongo"
export INSTALLDIR=$RPM_BUILD_DIR/install
export TOOLS_TAGS="ssl sasl"
export PORTABLE=1
export USE_SSE=1
export PATH=/usr/local/go/bin:$PATH

# RocksDB
pushd $RPM_BUILD_DIR/%{src_dir}/src/third_party/rocksdb
make -j4 EXTRA_CFLAGS='-fPIC -DLZ4 -I../lz4-r131 -DSNAPPY -I../snappy-1.1.3 -DHAVE_SSE42' EXTRA_CXXFLAGS='-fPIC -DLZ4 -I../lz4-r131 -DSNAPPY -I../snappy-1.1.3 -DHAVE_SSE42' DISABLE_JEMALLOC=1 static_lib
rm -rf ${INSTALLDIR}
mkdir -p ${INSTALLDIR}/include
mkdir -p ${INSTALLDIR}/bin
mkdir -p ${INSTALLDIR}/lib
make install-static INSTALL_PATH=${INSTALLDIR}
popd

# Build PSfMDB with SCons
pushd $RPM_BUILD_DIR/%{src_dir}
buildscripts/scons.py CC=${CC} CXX=${CXX} --audit --release --ssl --opt=on  \
%{?_smp_mflags} --use-sasl-client CPPPATH=${INSTALLDIR}/include LIBPATH=${INSTALLDIR}/lib \
--rocksdb --wiredtiger --inmemory --hotbackup ${PSM_TARGETS}
popd

# Mongo Tools compilation
pushd $RPM_BUILD_DIR/%{src_dir}/mongo-tools
. ./set_gopath.sh
. ./set_tools_revision.sh
rm -rf $RPM_BUILD_DIR/%{src_dir}/mongo-tools/vendor/pkg
mkdir -p $RPM_BUILD_DIR/%{src_dir}/bin
for tool in bsondump mongostat mongofiles mongoexport mongoimport mongorestore mongodump mongotop mongoreplay; do
  go build -a -x -o $RPM_BUILD_DIR/%{src_dir}/bin/${tool} -ldflags "-X github.com/mongodb/mongo-tools/common/options.Gitspec=${PSMDB_TOOLS_COMMIT_HASH} -X github.com/mongodb/mongo-tools/common/options.VersionStr=${PSMDB_TOOLS_REVISION}" -tags "${TOOLS_TAGS}" $RPM_BUILD_DIR/%{src_dir}/mongo-tools/${tool}/main/${tool}.go
done
popd

%install
#
rm -rf %{buildroot}
#
install -m 755 -d %{buildroot}/etc/selinux/targeted/modules/active/modules
install -m 644 %{SOURCE6} %{buildroot}/etc/selinux/targeted/modules/active/modules/
#
install -m 755 -d %{buildroot}/%{_bindir}
install -m 755 -d %{buildroot}/%{_sysconfdir}
install -m 755 -d %{buildroot}/%{_mandir}/man1

install -m 750 -d %{buildroot}/var/log/mongo
touch %{buildroot}/var/log/mongo/mongod.log
install -m 750 -d %{buildroot}/%{mongo_home}
install -m 755 -d %{buildroot}/%{_sysconfdir}/sysconfig
#
install -m 644 %{SOURCE1} %{buildroot}/%{_sysconfdir}/mongod.conf
sed -i 's:mongodb:mongo:g' %{buildroot}/%{_sysconfdir}/mongod.conf
# startup stuff
install -m 755 -d %{buildroot}/etc/init.d
install -m 750 %{SOURCE5} %{buildroot}/etc/init.d/mongod
#

install -m 755 -d %{buildroot}/%{_unitdir}
install -m 644 %{SOURCE2} %{buildroot}/%{_unitdir}/mongod.service

install -m 644 %{SOURCE3} %{buildroot}/%{_sysconfdir}/sysconfig/mongod
install -m 755 %{SOURCE4} %{buildroot}/%{_bindir}/
install -m 755 %{SOURCE7} %{buildroot}/%{_bindir}/
#
install -m 755 mongo %{buildroot}/%{_bindir}/
install -m 755 mongod %{buildroot}/%{_bindir}/
install -m 755 mongos %{buildroot}/%{_bindir}/

install -m 755 $RPM_BUILD_DIR/%{src_dir}/bin/* %{buildroot}/%{_bindir}/

install -m 644 $RPM_BUILD_DIR/%{src_dir}/manpages/* %{buildroot}/%{_mandir}/man1/

%files

%files mongos
%defattr(-,root,root,-)
%{_bindir}/mongos
%{_mandir}/man1/mongos.1.gz

%files server
%defattr(-,root,root,-)
%{_bindir}/mongod
%{_mandir}/man1/mongod.1.gz
%{_bindir}/percona-server-mongodb-helper.sh
%{_bindir}/percona-server-mongodb-enable-auth.sh
/etc/init.d/mongod
%{_unitdir}/mongod.service
/etc/selinux/targeted/modules/active/modules/mongod.pp
%attr(0750,mongod,mongod) %dir %{mongo_home}
%attr(0750,mongod,mongod) %dir /var/log/mongo
%config(noreplace) %{_sysconfdir}/mongod.conf
%config(noreplace) %{_sysconfdir}/sysconfig/mongod
%attr(0640,mongod,mongod) %ghost /var/log/mongo/mongod.log
%doc LICENSE-Community.txt README THIRD-PARTY-NOTICES

%files shell
%defattr(-,root,root,-)
%{_bindir}/mongo
%{_mandir}/man1/mongo.1.gz

%files tools
%defattr(-,root,root,-)
%{_bindir}/bsondump
%{_mandir}/man1/bsondump.1.gz
%{_bindir}/mongostat
%{_mandir}/man1/mongostat.1.gz
%{_bindir}/mongofiles
%{_mandir}/man1/mongofiles.1.gz
%{_bindir}/mongoexport
%{_mandir}/man1/mongoexport.1.gz
%{_bindir}/mongoimport
%{_mandir}/man1/mongoimport.1.gz
%{_bindir}/mongorestore
%{_mandir}/man1/mongorestore.1.gz
%{_bindir}/mongodump
%{_mandir}/man1/mongodump.1.gz
%{_bindir}/mongotop
%{_mandir}/man1/mongotop.1.gz
%{_bindir}/mongoreplay

%pre server
if [ $1 == 1 ]; then
  if ! getent passwd mongod > /dev/null 2>&1; then
    /usr/sbin/groupadd -r mongod
    /usr/sbin/useradd -M -r -g mongod -d %{mongo_home} -s /bin/false -c mongod mongod > /dev/null 2>&1
  fi
fi

if [ $1 -gt 1 ]; then
    STATUS_FILE=/tmp/MONGO_RPM_UPGRADE_MARKER
    PID=$(ps wwaux | grep /usr/bin/mongod | grep -v grep | awk '{print $2}')
    if [  -z $PID ]; then
        echo "SERVER_TO_START=0"    >> $STATUS_FILE
    else
        echo "SERVER_TO_START=1"    >> $STATUS_FILE
    fi
fi
#

%post server
#
/sbin/chkconfig --add mongod
%systemd_post mongod.service
echo " * To start the service, configure your engine and start mongod"
parse_yaml() {
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\)\($w\)$s:$s\"\(.*\)\"$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
   awk -F$fs '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s=\"%s\"\n", vn, $2, $3);
      }
   }'
}

array=$(parse_yaml /etc/mongod.conf)
result=0
while IFS=' ' read -ra VALUES; do
    for value in "${VALUES[@]}"; do
        if [[ $value =~ ([^,]+).*"="\"([^,]+)\" ]]; then
            name=${BASH_REMATCH[1]}
            val=${BASH_REMATCH[2]}
        fi
        if [[ $name =~ security && $name =~ auth ]]; then
            result=$val
            break
        fi
    done
done <<< "$array"
AUTH_ENABLED=0
if [[ $result == enabled  ]]; then
    AUTH_ENABLED=1
elif [[ $result == disabled  ]]; then
    AUTH_ENABLED=0
elif [[ `egrep '^auth=1' /etc/mongod.conf` ]]; then
    AUTH_ENABLED=1
elif [[ `egrep '^auth=0' /etc/mongod.conf` ]]; then
    AUTH_ENABLED=0
fi

if [[ $AUTH_ENABLED == 0 ]]; then
    echo " ** WARNING: Access control is not enabled for the database."
    echo " ** Read and write access to data and configuration is unrestricted."
    echo " ** To fix this please use /usr/bin/percona-server-mongodb-enable-auth.sh "
fi
if [ $1 -gt 1 ]; then
    STATUS_FILE=/tmp/MONGO_RPM_UPGRADE_MARKER
    if [ -f $STATUS_FILE ] ; then
            SERVER_TO_START=`grep '^SERVER_TO_START=' $STATUS_FILE | cut -c17-`
            rm -f $STATUS_FILE
    else
            SERVER_TO_START=''
    fi
    if [ $SERVER_TO_START == 1 ]; then
        if [ -x %{_sysconfdir}/init.d/mongod ] ; then
            %{_sysconfdir}/init.d/mongod restart
        fi
    fi
fi

%preun server
%systemd_preun mongod.service
if [ -x %{_sysconfdir}/init.d/mongod ] ; then
  %{_sysconfdir}/init.d/mongod stop
fi
/sbin/chkconfig --del mongod

%postun server
%systemd_postun mongod.service
/sbin/service mongod condrestart >/dev/null 2>&1 || :
if [ $1 == 0 ]; then
  if /usr/bin/id -g mongod > /dev/null 2>&1; then
    /usr/sbin/userdel mongod > /dev/null 2>&1
    /usr/sbin/groupdel mongod > /dev/null 2>&1 || true
  fi
fi

#
%changelog

* Wed May 31 2017 Evgeniy Patlan <evgeniy.patlan@percona.com> 3.4
- Initial RPM release for Percona Server for MongoDB for sles
