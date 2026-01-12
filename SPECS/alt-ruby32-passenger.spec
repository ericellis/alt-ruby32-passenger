%define debug_package %{nil}
%define _enable_debug_packages %{nil}

# Defining the package namespace
%global ns_name alt
%global ns_dir /opt/alt
%global pkg ruby32
%global gem_name passenger
%global bundled_boost_version 1.87.0

# Force Software Collections on
%global _scl_prefix %{ns_dir}
%global scl %{ns_name}-%{pkg}
# HACK: OBS Doesn't support macros in BuildRequires statements, so we have
#       to hard-code it here.
# https://en.opensuse.org/openSUSE:Specfile_guidelines#BuildRequires
%global scl_prefix %{scl}-
%{?scl:%scl_package rubygem-%{gem_name}}

%global passenger_libdir    %{_datadir}/passenger
%global passenger_archdir   %{_libdir}/passenger
%global passenger_agentsdir %{_libexecdir}/passenger
%define ruby_vendorlibdir   %(scl enable alt-ruby32 "ruby -rrbconfig -e 'puts RbConfig::CONFIG[%q|vendorlibdir|]'")

# Doing release_prefix this way for Release allows for OBS-proof versioning, See EA-4590 for more details
%define release_prefix 1

%global _httpd_mmn         %(cat %{_root_includedir}/apache2/.mmn 2>/dev/null || echo missing-ea-apache24-devel)
%global _httpd_confdir     %{_root_sysconfdir}/apache2/conf.d
%global _httpd_modconfdir  %{_root_sysconfdir}/apache2/conf.modules.d
%global _httpd_moddir      %{_root_libdir}/apache2/modules

%define ea_openssl_ver 1.1.1d-1
%define ea_libcurl_ver 7.68.0-2

Summary: Phusion Passenger application server
Name: %{?scl:%scl_prefix}rubygem-passenger
Version: 6.1.1
Release: %{release_prefix}%{?dist}.cpanel
Group: System Environment/Daemons
# Passenger code uses MIT license.
# Bundled(Boost) uses Boost Software License
# BCrypt and Blowfish files use BSD license.
# Documentation is CC-BY-SA
# See: https://bugzilla.redhat.com/show_bug.cgi?id=470696#c146
License: Boost and BSD and BSD with advertising and MIT and zlib
URL: https://www.phusionpassenger.com

# http://s3.amazonaws.com/phusion-passenger/releases/passenger-%%{version}.tar.gz
Source: release-%{version}.tar.gz
Source1: passenger.logrotate
Source2: rubygem-passenger.tmpfiles
Source3: cxxcodebuilder.tar.gz
Source10: apache-passenger.conf.in
Source12: config.json
# These scripts are needed only before we update httpd24-httpd.service
# in rhel7 to allow enabling extra SCLs.
Source13: alt-ruby32
Source14: passenger_apps.default
Source15: update_ruby_shebang.pl

# Use upstream libuv instead of the bundled libuv
Patch0:         0001-Patch-build-files-to-use-SCL-libuv-paths.patch
# httpd on RHEL7 is using private /tmp. This break passenger status.
# We workaround that by using "/var/run/alt-ruby32-passenger" instead of "/tmp".
Patch1:         0002-Avoid-using-tmp-for-the-TMPDIR.patch
# Load passenger_native_support.so from lib_dir
Patch2:         0003-Fix-the-path-for-passenger_native_support.patch
# Supress logging of empty messages
Patch3:         0004-Suppress-logging-of-empty-messages.patch
# Update the instance registry paths to include the SCL path
Patch4:         0005-Add-the-instance-registry-path-for-the-alt-ruby32-SCL.patch
# Build against ea-libcurl
Patch5:         0006-Use-ea-libcurl-instead-of-system-curl.patch
# Add a new directive to Passenger that will allow us to disallow
## Passenger directives in .htaccess files
Patch6:         0007-Add-new-PassengerDisableHtaccess-directive.patch

BuildRequires: tree

BuildRequires: ea-apache24-devel
BuildRequires: %{?scl:%scl_prefix}ruby
BuildRequires: %{?scl:%scl_prefix}ruby-devel
BuildRequires: %{?scl:%scl_prefix}rubygems
BuildRequires: %{?scl:%scl_prefix}rubygems-devel
BuildRequires: %{?scl:%scl_prefix}rubygem(rake) >= 0.8.1
BuildRequires: %{?scl:%scl_prefix}rubygem(rack)
Requires: %{?scl:%scl_prefix}rubygem(rack)
# Required for testing, but tests are disabled cause they failed.
BuildRequires: %{?scl:%scl_prefix}rubygem(sqlite3)
BuildRequires: %{?scl:%scl_prefix}rubygem(mizuho)

BuildRequires: perl

%if 0%{?rhel} < 8
BuildRequires: ea-libcurl >= %{ea_libcurl_ver}
BuildRequires: ea-libcurl-devel >= %{ea_libcurl_ver}
BuildRequires: ea-brotli ea-brotli-devel
BuildRequires: ea-openssl11 >= %{ea_openssl_ver}
BuildRequires: ea-openssl11-devel >= %{ea_openssl_ver}
%else
BuildRequires: curl
BuildRequires: libcurl
BuildRequires: libcurl-devel
BuildRequires: brotli
BuildRequires: brotli-devel
BuildRequires: openssl-devel
BuildRequires: libnghttp2
BuildRequires: python2
Requires: python2
%endif

%if 0%{?rhel} >= 8
# NOTE: our macros.scl insists that I use python3.  Too much risk on the
# scripts
%global __os_install_post %{expand:
    /usr/lib/rpm/brp-scl-compress %{_scl_root}
    %{!?__debug_package:/usr/lib/rpm/brp-strip %{__strip}
    /usr/lib/rpm/brp-strip-comment-note %{__strip} %{__objdump}
    }
    /usr/lib/rpm/brp-strip-static-archive %{__strip}
    /usr/lib/rpm/brp-scl-python-bytecompile /usr/bin/python2 %{?_python_bytecompile_errors_terminate_build} %{_scl_root}
    /usr/lib/rpm/brp-python-hardlink
%{nil}}
%endif

BuildRequires: zlib-devel
BuildRequires: pcre-devel
BuildRequires: %{?scl:%scl_prefix}libuv-devel

BuildRequires: scl-utils
BuildRequires: scl-utils-build
%{?scl:BuildRequires: %{scl}-runtime}
%{?scl:Requires:%scl_runtime}

%if 0%{?rhel} < 8
Requires: ea-libcurl >= %{ea_libcurl_ver}
Requires: ea-openssl11 >= %{ea_openssl_ver}
%else
Requires: libcurl
Requires: openssl
%endif

Provides: bundled(boost) = %{bundled_boost_version}

# Suppress auto-provides for module DSO
%{?filter_provides_in: %filter_provides_in %{_httpd_moddir}/.*\.so$}
%{?filter_setup}

%description
Phusion Passenger(r) is a web server and application server, designed to be fast,
robust and lightweight. It takes a lot of complexity out of deploying web apps,
adds powerful enterprise-grade features that are useful in production,
and makes administration much easier and less complex. It supports Ruby,
Python, Node.js and Meteor.

%package -n %{scl_prefix}mod_passenger
Summary: Apache Module for Phusion Passenger
Group: System Environment/Daemons
BuildRequires:  ea-apache24-devel
Requires: ea-apache24-mmn = %{_httpd_mmn}
Requires: %{scl_prefix}ruby-wrapper
Requires: %{name}%{?_isa} = %{version}-%{release}
License: Boost and BSD and BSD with advertising and MIT and zlib
Provides: apache24-passenger
Conflicts: apache24-passenger

%description -n %{scl_prefix}mod_passenger
This package contains the pluggable Apache server module for Phusion Passenger(r).

%package doc
Summary: Phusion Passenger documentation
Group: System Environment/Daemons
Requires: %{name} = %{version}-%{release}
BuildArch: noarch
License: CC-BY-SA and MIT and (MIT or GPL+)

%description doc
This package contains documentation files for Phusion Passenger(r).

%package -n %{?scl:%scl_prefix}ruby-wrapper
Summary:   Phusion Passenger application server for %{scl_prefix}
Requires: %{name}%{?_isa} = %{version}-%{release}
Requires: %{?scl:%scl_prefix}ruby

%description -n %{?scl:%scl_prefix}ruby-wrapper
Phusion Passenger application server for %{scl_prefix}.

%prep
%setup -q %{?scl:-n %{gem_name}-release-%{version}}

%patch0 -p1 -b .libuv
%patch1 -p1 -b .tmpdir
%patch2 -p1 -b .nativelibdir
%patch3 -p1 -b .emptymsglog
%patch4 -p1 -b .instanceregpath
%if 0%{?rhel} < 8
%patch5 -p1 -b .useeacurl
%endif
%patch6 -p1 -b .disablehtaccess
cp %{SOURCE15} .

tar -xf %{SOURCE3}

# Don't use bundled libuv
rm -rf src/cxx_supportlib/vendor-modified/libuv

# Find files with a hash-bang that do not have executable permissions
for script in `find . -type f ! -perm /a+x -name "*.rb"`; do
    [ ! -z "`head -n 1 $script | grep \"^#!/\"`" ] && chmod -v 755 $script
    /bin/true
done

%build
# Build the complete Passenger and shared module against ruby32.

%{?scl:scl enable alt-ruby32 - << \EOF}
export LD_LIBRARY_PATH=%{_libdir}:$LD_LIBRARY_PATH
export USE_VENDORED_LIBEV=true
export USE_VENDORED_LIBUV=false
export GEM_PATH=%{gem_dir}:${GEM_PATH:+${GEM_PATH}}${GEM_PATH:-`scl enable alt-ruby32 -- ruby -e "print Gem.path.join(':')"`}
CFLAGS="${CFLAGS:-%optflags}" ; export CFLAGS ;
CXXFLAGS="${CXXFLAGS:-%optflags}" ; export CXXFLAGS ;
%if 0%{?rhel} < 8
EXTRA_CXX_LDFLAGS="-L/opt/alt/ruby32/root/usr/lib64 -L/opt/cpanel/ea-openssl11/%{_lib} -L/opt/cpanel/ea-brotli/%{_lib} -Wl,-rpath=/opt/cpanel/ea-openssl11/%{_lib} -Wl,-rpath=/opt/cpanel/ea-brotli/%{_lib} -Wl,-rpath=/opt/cpanel/libcurl/%{_lib}  -Wl,-rpath=%{_libdir},--enable-new-dtags "; export EXTRA_CXX_LDFLAGS;
%else
EXTRA_CXX_LDFLAGS="-L/opt/alt/ruby32/root/usr/lib64 -L/usr/lib64 -lcurl -lssl -lcrypto -lgssapi_krb5 -lkrb5 -lk5crypto -lkrb5support -lssl -lcrypto -lssl -lcrypto -Wl,-rpath=%{_libdir},--enable-new-dtags -lssl -lcrypto -lssl -lcrypto -lssl -lcrypto -lssl -lcrypto -lssl -lcrypto "; export EXTRA_CXX_LDFLAGS;
%endif

FFLAGS="${FFLAGS:-%optflags}" ; export FFLAGS;

%if 0%{?rhel} < 8
export EXTRA_CXXFLAGS="-I/opt/cpanel/ea-openssl11/include -I/opt/cpanel/libcurl/include -I/opt/alt/ruby32/root/usr/include"
%else
export EXTRA_CXXFLAGS="-I/opt/alt/ruby32/root/usr/include -I/usr/include"
%endif

export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

rake fakeroot \
    NATIVE_PACKAGING_METHOD=rpm \
    FS_PREFIX=%{_prefix} \
    FS_BINDIR=%{_bindir} \
    FS_SBINDIR=%{_sbindir} \
    FS_DATADIR=%{_datadir} \
    FS_LIBDIR=%{_libdir} \
    FS_DOCDIR=%{_docdir} \
    RUBYLIBDIR=%{passenger_libdir} \
    RUBYARCHDIR=%{passenger_archdir} \
    APACHE2_MODULE_PATH=%{_httpd_moddir}/mod_passenger.so

%{?scl:EOF}

# find python and ruby scripts to change their shebang

find . -name "*.py" -print | xargs sed -i '1s:^#!.*python.*$:#!/usr/bin/python2:'

find . -name "*.rb" -print | xargs sed -i '1s:^#!.*ruby.*$:#!/opt/alt/ruby32/root/usr/bin/ruby:'

%install

mkdir -p %{buildroot}/opt/alt/ruby32/src/passenger-release-%{version}/
tar xzf %{SOURCE0} -C %{buildroot}/opt/alt/ruby32/src/
tar xzf %{SOURCE3} -C %{buildroot}/opt/alt/ruby32/src/passenger-release-%{version}/

# Remove test directories that contain Python 3 syntax incompatible with Python 2 byte-compilation
rm -rf %{buildroot}/opt/alt/ruby32/src/passenger-release-%{version}/test/

%{?scl:scl enable alt-ruby32 - << \EOF}
export USE_VENDORED_LIBEV=true
export USE_VENDORED_LIBUV=false

export LANG=en_US.UTF-8
export LANGUAGE=en_US.UTF-8
export LC_ALL=en_US.UTF-8

cp -a pkg/fakeroot/* %{buildroot}/

# Install bootstrapping code into the executables and the Nginx config script.
./dev/install_scripts_bootstrap_code.rb --ruby %{passenger_libdir} %{buildroot}%{_bindir}/* %{buildroot}%{_sbindir}/*
%{?scl:EOF}

# Install Apache module.
mkdir -p %{buildroot}/%{_httpd_moddir}
install -pm 0755 buildout/apache2/mod_passenger.so %{buildroot}/%{_httpd_moddir}

# Install Apache config.
mkdir -p %{buildroot}%{_httpd_confdir} %{buildroot}%{_httpd_modconfdir}
sed -e 's|@PASSENGERROOT@|%{passenger_libdir}/phusion_passenger/locations.ini|g' %{SOURCE10} > passenger.conf
sed -i 's|@PASSENGERDEFAULTRUBY@|%{_libexecdir}/passenger-ruby32|g' passenger.conf
sed -i 's|@PASSENGERSO@|%{_httpd_moddir}/mod_passenger.so|g' passenger.conf
sed -i 's|@PASSENGERINSTANCEDIR@|%{_localstatedir}/run/passenger-instreg|g' passenger.conf

mkdir -p %{buildroot}/var/cpanel/templates/apache2_4
# keep version agnostic name for old ULCs :(
install -m 0640 %{SOURCE14} %{buildroot}/var/cpanel/templates/apache2_4/passenger_apps.default
# have version/package specific name for new ULCs :)
install -m 0640 %{SOURCE14} %{buildroot}/var/cpanel/templates/apache2_4/ruby32-mod_passenger.appconf.default

mkdir -p %{buildroot}/etc/cpanel/ea4
echo -n %{_libexecdir}/passenger-ruby32 > %{buildroot}/etc/cpanel/ea4/passenger.ruby

# do python3 (and not worry about systems w/ only /usr/bin/python) because:
#    1. python3 is not EOL
#    2. /usr/bin/python is no longer a thing in python land
#    3. if they didn't have this configure their python app is broken anyway
#    4. They can configure this if they really want /usr/bin/python, /usr/bin/python2, /usr/bin/python3.6, etc
echo -n "/usr/bin/python3" > %{buildroot}/etc/cpanel/ea4/passenger.python

%if "%{_httpd_modconfdir}" != "%{_httpd_confdir}"
    sed -n /^LoadModule/p passenger.conf > 10-passenger.conf
    sed -i /^LoadModule/d passenger.conf
    touch -r %{SOURCE10} 10-passenger.conf
    install -pm 0644 10-passenger.conf %{buildroot}%{_httpd_modconfdir}/passenger.conf
%endif
touch -r %{SOURCE10} passenger.conf
install -pm 0644 passenger.conf %{buildroot}%{_httpd_confdir}/passenger.conf

# Install wrapper script to allow using the SCL Ruby binary via apache
%{__mkdir_p} %{buildroot}%{_libexecdir}/
install -pm 0755 %{SOURCE13} %{buildroot}%{_libexecdir}/passenger-ruby32

# Move agents to libexec
mkdir -p %{buildroot}/%{passenger_agentsdir}
mv %{buildroot}/%{passenger_archdir}/support-binaries/* %{buildroot}/%{passenger_agentsdir}
rmdir %{buildroot}/%{passenger_archdir}/support-binaries/
sed -i 's|%{passenger_archdir}/support-binaries|%{passenger_agentsdir}|g' \
    %{buildroot}%{passenger_libdir}/phusion_passenger/locations.ini

# Instance registry to track apps
mkdir -p %{buildroot}%{_localstatedir}/run/passenger-instreg

# tmpfiles.d
%if 0%{?rhel} > 6
    mkdir -p %{buildroot}/var/run
    mkdir -p %{buildroot}%{_root_prefix}/lib/tmpfiles.d
    install -m 0644 %{SOURCE2} %{buildroot}%{_root_prefix}/lib/tmpfiles.d/%{scl_prefix}passenger.conf
    install -d -m 0755 %{buildroot}/var/run/%{scl_prefix}passenger
%else
    mkdir -p %{buildroot}/var/run/%{scl_prefix}passenger
%endif

# Install man pages into the proper location.
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_mandir}/man8
cp man/*.1 %{buildroot}%{_mandir}/man1
cp man/*.8 %{buildroot}%{_mandir}/man8

# Fix Python scripts with shebang which are not executable
chmod +x %{buildroot}%{_datadir}/passenger/helper-scripts/wsgi-loader.py

# Remove empty release.txt file
rm -f %{buildroot}%{_datadir}/passenger/release.txt

# Remove object files and source files. They are needed to compile nginx
# using "passenger-install-nginx-module", but it's not according to
# guidelines. Debian does not provide these files too, so we stay consistent.
# In the long term, it would be better to allow Fedora nginx to support
# Passenger.
rm -rf %{buildroot}%{passenger_libdir}/ngx_http_passenger_module
rm -rf %{buildroot}%{passenger_libdir}/ruby_extension_source
rm -rf %{buildroot}%{passenger_libdir}/include
rm -rf %{buildroot}%{passenger_archdir}/nginx_dynamic
rm -rf %{buildroot}%{_libdir}/passenger/common
rm -rf %{buildroot}%{_bindir}/passenger-install-*-module

mkdir -p %{buildroot}%{ruby_vendorlibdir}/passenger
cp %{buildroot}/%{passenger_archdir}/*.so %{buildroot}%{ruby_vendorlibdir}/passenger/

cd %{buildroot}/opt/alt/ruby32/src
perl %{SOURCE15}
cd -

%check
%{?scl:scl enable alt-ruby32 - << \EOF}
export USE_VENDORED_LIBEV=true
export USE_VENDORED_LIBUV=false

# Running the full test suite is not only slow, but also impossible
# because not all requirements are packaged by Fedora. It's also not
# too useful because Phusion Passenger is automatically tested by a CI
# server on every commit. The C++ tests are the most likely to catch
# any platform-specific bugs (e.g. bugs caused by wrong compiler options)
# so we only run those. Note that the C++ tests are highly timing
# sensitive, so sometimes they may fail even though nothing is really
# wrong. We therefore do not make failures fatal, although the result
# should still be checked.
# Currently the tests fail quite often on ARM because of the slower machines.
# Test are not included in the tarballs now :'(
# cp %{SOURCE12} test/config.json
# rake test:cxx || true
%{?scl:EOF}

%pre -n %{scl_prefix}mod_passenger

if [ -e "%{_localstatedir}/lib/rpm-state/alt-ruby32-passenger/has_python_conf" ] ; then
    unlink %{_localstatedir}/lib/rpm-state/alt-ruby32-passenger/has_python_conf
fi

if [ -e "/etc/cpanel/ea4/passenger.python" ] ; then
    echo "Has existing python configuration, will leave that as is …"
    mkdir -p %{_localstatedir}/lib/rpm-state/alt-ruby32-passenger
    touch %{_localstatedir}/lib/rpm-state/alt-ruby32-passenger/has_python_conf
else
    echo "Will verify new python configuration …"
fi

%posttrans -n %{scl_prefix}mod_passenger

if [ ! -f "%{_localstatedir}/lib/rpm-state/alt-ruby32-passenger/has_python_conf" ] ; then
    echo "… Ensuring new python configuration is valid …";
    if [ ! -x "/usr/bin/python3" ] ; then
        echo "… no python3, trying python …"
        if [ -x "/usr/bin/python" ] ; then
            echo "… using python";
            echo -n "/usr/bin/python" > /etc/cpanel/ea4/passenger.python
        else
            echo "… no python, removing value";
            echo -n "" > /etc/cpanel/ea4/passenger.python
        fi
    fi
else
    echo "… using previous python configuration"
fi

RESTART_NEEDED=""
PERL=/usr/local/cpanel/3rdparty/bin/perl
UPDATE_USERDATA='my ($y, $r)=@ARGV;my $u="";my $apps=eval {Cpanel::JSON::LoadFile($y)}; if ($@) { warn $@; exit 0 } for my $app (keys %{$apps}) { if(!$apps->{$app}{ruby}) { $apps->{$app}{ruby} = $r;if(!$u) { $u=$y;$u=~ s{/[^/]+$}{};$u=~s{/var/cpanel/userdata/}{}; } } } Cpanel::JSON::DumpFile($y, $apps);print $u'
UPDATE_INCLUDES='my $ch="";my $obj=Cpanel::Config::userdata::PassengerApps->new({user=>$ARGV[0]});my $apps=$obj->list_applications();for my $name (keys %{$apps}) {my $data=$apps->{$name};if ($data->{enabled}) {$obj->generate_apache_conf($name);$ch++;}}print $ch;'

for appconf in $(ls /var/cpanel/userdata/*/applications.json 2>/dev/null); do
    REGEN_USER=$($PERL -MCpanel::JSON -e "$UPDATE_USERDATA" $appconf /opt/alt/ruby32/root/usr/libexec/passenger-ruby32)

    if [ ! -z "$REGEN_USER" ]; then
        MADE_CHANGES=$($PERL -MCpanel::Config::userdata::PassengerApps -e "$UPDATE_INCLUDES" $REGEN_USER)

        if [ ! -z "$MADE_CHANGES" ]; then
            RESTART_NEEDED=1

            if [ -x "/usr/local/cpanel/scripts/ea-nginx" ]; then
                /usr/local/cpanel/scripts/ea-nginx config $REGEN_USER --no-reload
            fi
        fi
    fi
done

if [ ! -z "$RESTART_NEEDED" ]; then
   /usr/local/cpanel/scripts/restartsrv_httpd --restart

   if [ -x "/usr/local/cpanel/scripts/ea-nginx" ]; then
       /usr/local/cpanel/scripts/ea-nginx reload
   fi
fi

%files
%doc LICENSE CONTRIBUTORS CHANGELOG
%{_bindir}/passenger*
%if 0%{?rhel} > 6
%{_root_prefix}/lib/tmpfiles.d/*.conf
%endif
%dir /var/run/%{scl_prefix}passenger
%dir %attr(755, root, root) %{_localstatedir}/run/passenger-instreg
%{passenger_libdir}
%{passenger_archdir}
%{passenger_agentsdir}
%{ruby_vendorlibdir}/passenger/
%{_sbindir}/*
%{_mandir}/man1/*
%{_mandir}/man8/*

%files -n %{?scl:%scl_prefix}ruby-wrapper
%doc LICENSE CONTRIBUTORS CHANGELOG
%{_libexecdir}/passenger-ruby32

%files doc
%doc %{_docdir}/passenger

%files -n %{scl_prefix}mod_passenger
%config(noreplace) %{_httpd_modconfdir}/*.conf
%if "%{_httpd_modconfdir}" != "%{_httpd_confdir}"
%config(noreplace) %{_httpd_confdir}/*.conf
%endif
/var/cpanel/templates/apache2_4/passenger_apps.default
/var/cpanel/templates/apache2_4/ruby32-mod_passenger.appconf.default
/etc/cpanel/ea4/passenger.ruby
%config(noreplace) /etc/cpanel/ea4/passenger.python
%{_httpd_moddir}/mod_passenger.so
/opt/alt/ruby32/src/passenger-release-%{version}/

%changelog
* Sun Jan 12 2026 Your Name <your.email@example.com> - 6.1.1-1
- Ported to alt-ruby32 from ea-ruby27-passenger

* Tue Dec 23 2025 Cory McIntire <cory.mcintire@webpros.com> - 6.1.1-1
- EA-13307: Update ea-ruby27-passenger from v6.1.0 to v6.1.1

* Fri Nov 21 2025 Cory McIntire <cory.mcintire@webpros.com> - 6.1.0-2
- EA-13227: Disable CentOS 7 builds (Passenger 6.1.0 requires C++11 features not in GCC 4.8)

* Tue Oct 21 2025 Cory McIntire <cory.mcintire@webpros.com> - 6.1.0-1
- EA-13227: Update ea-ruby27-passenger from v6.0.27 to v6.1.0

* Mon Oct 06 2025 Brian Mendoza <brian.mendoza@cpanel.net> - 6.0.27-1
- EA-12915: Update ea-ruby27-passenger from v6.0.23 to v6.0.27

* Thu Aug 01 2024 Cory McIntire <cory@cpanel.net> - 6.0.23-1
- EA-12309: Update ea-ruby27-passenger from v6.0.22 to v6.0.23

* Sat May 18 2024 Cory McIntire <cory@cpanel.net> - 6.0.22-1
- EA-12162: Update ea-ruby27-passenger from v6.0.20 to v6.0.22

* Mon Jan 22 2024 Cory McIntire <cory@cpanel.net> - 6.0.20-1
- EA-11927: Update ea-ruby27-passenger from v6.0.19 to v6.0.20

* Wed Nov 29 2023 Cory McIntire <cory@cpanel.net> - 6.0.19-1
- EA-11828: Update ea-ruby27-passenger from v6.0.18 to v6.0.19

* Fri Jun 16 2023 Cory McIntire <cory@cpanel.net> - 6.0.18-1
- EA-11500: Update ea-ruby27-passenger from v6.0.17 to v6.0.18

* Wed May 17 2023 Julian Brown <julian.brown@cpanel.net> - 6.0.17-3
- ZC-10950: Fix build problems

* Tue May 09 2023 Brian Mendoza <brian.mendoza@cpanel.net> - 6.0.17-2
- ZC-10936: Clean up Makefile and remove debug-package-nil

* Sun Jan 29 2023 Cory McIntire <cory@cpanel.net> - 6.0.17-1
- EA-11188: Update ea-ruby27-passenger from v6.0.16 to v6.0.17

* Wed Dec 21 2022 Cory McIntire <cory@cpanel.net> - 6.0.16-1
- EA-11117: Update ea-ruby27-passenger from v6.0.15 to v6.0.16

* Wed Sep 21 2022 Cory McIntire <cory@cpanel.net> - 6.0.15-1
- EA-10946: Update ea-ruby27-passenger from v6.0.14 to v6.0.15

* Wed May 11 2022 Cory McIntire <cory@cpanel.net> - 6.0.14-1
- EA-10701: Update ea-ruby27-passenger from v6.0.13 to v6.0.14

* Tue Apr 19 2022 Travis Holloway <t.holloway@cpanel.net> - 6.0.13-2
- EA-10531: Suppress no such file or directory warning during install

* Fri Apr 01 2022 Cory McIntire <cory@cpanel.net> - 6.0.13-1
- EA-10603: Update ea-ruby27-passenger from v6.0.12 to v6.0.13

* Tue Dec 28 2021 Dan Muey <dan@cpanel.net> - 6.0.12-2
- ZC-9589: Update DISABLE_BUILD to match OBS

* Mon Nov 08 2021 Travis Holloway <t.holloway@cpanel.net> - 6.0.12-1
- EA-10264: Update ea-ruby27-passenger from v6.0.11 to v6.0.12

* Mon Oct 04 2021 Cory McIntire <cory@cpanel.net> - 6.0.11-1
- EA-10161: Update ea-ruby27-passenger from v6.0.10 to v6.0.11

* Mon Jul 19 2021 Cory McIntire <cory@cpanel.net> - 6.0.10-1
- EA-9973: Update ea-ruby27-passenger from v6.0.9 to v6.0.10

* Mon Jun 14 2021 Cory McIntire <cory@cpanel.net> - 6.0.9-1
- EA-9860: Update ea-ruby27-passenger from v6.0.8 to v6.0.9

* Wed Jun 02 2021 Julian Brown <julian.brown@cpanel.net> - 6.0.8-1
- EA-9803: Update ea-ruby27-passenger from v6.0.7 to v6.0.8

* Thu Feb 25 2021 Cory McIntire <cory@cpanel.net> - 6.0.7-1
- EA-9604: Update ea-ruby27-passenger from v6.0.6 to v6.0.7

* Mon Dec 28 2020 Daniel Muey <dan@cpanel.net> - 6.0.6-6
- ZC-8188: provide `/etc/cpanel/ea4/passenger.python`

* Mon Dec 07 2020 Daniel Muey <dan@cpanel.net> - 6.0.6-5
- ZC-7897: Add version/package specific template file (and support userdata paths like nginx)

* Mon Dec 07 2020 Travis Holloway <t.holloway@cpanel.net> - 6.0.6-4
- ZC-8082: Do not apply ea-libcurl patch on C8 builds

* Mon Dec 07 2020 Daniel Muey <dan@cpanel.net> - 6.0.6-3
- ZC-7655: Provide/Conflict `apache24-passenger`

* Tue Dec 01 2020 Julian Brown <julian.brown@cpanel.net> - 6.0.6-2
- ZC-7974: Require rack

* Tue Sep 08 2020 Julian Brown <julian.brown@cpanel.net> - 6.0.6-1
- ZC-7508: Initial Commit
