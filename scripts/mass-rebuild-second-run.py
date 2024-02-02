#!/usr/bin/python3
#
# mass-rebuild-second-run.py
# To run mass rebuild for the second time on a set of packages
#
# Copyright (C) 2009-2020 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#     Mohan Boddu <mboddu@bhujji.com>
#

from __future__ import print_function
import koji
import os
import subprocess
import sys
import operator

# contains info about all rebuilds, add new rebuilds there and update rebuildid
# here
from massrebuildsinfo import MASSREBUILDS

# Set some variables
# Some of these could arguably be passed in as args.
rebuildid = 'f35'
massrebuild = MASSREBUILDS[rebuildid]
user = 'Fedora Release Engineering <releng@fedoraproject.org>'
comment = 'Second attempt - Rebuilt for ' + massrebuild['wikipage']
workdir = os.path.expanduser('~/massbuild')
enviro = os.environ


# Define functions

# This function needs a dry-run like option
def runme(cmd, action, pkg, env, cwd=workdir):
    """Simple function to run a command and return 0 for success, 1 for
       failure.  cmd is a list of the command and arguments, action is a
       name for the action (for logging), pkg is the name of the package
       being operated on, env is the environment dict, and cwd is where
       the script should be executed from."""

    try:
        subprocess.check_call(cmd, env=env, cwd=cwd)
    except subprocess.CalledProcessError as e:
        sys.stderr.write('%s failed %s: %s\n' % (pkg, action, e))
        return 1
    return 0

# This function needs a dry-run like option
def runmeoutput(cmd, action, pkg, env, cwd=workdir):
    """Simple function to run a command and return output if successful. 
       cmd is a list of the command and arguments, action is a
       name for the action (for logging), pkg is the name of the package
       being operated on, env is the environment dict, and cwd is where
       the script should be executed from.  Returns 0 for failure"""

    try:
        pid = subprocess.Popen(cmd, env=env, cwd=cwd,
                               stdout=subprocess.PIPE, encoding='utf8')
    except BaseException as e:
        sys.stderr.write('%s failed %s: %s\n' % (pkg, action, e))
        return 0
    result = pid.communicate()[0].rstrip('\n')
    return result


# Environment for using releng credentials for pushing and building
enviro['GIT_SSH'] = '/usr/local/bin/relengpush'
koji_bin = '/usr/bin/compose-koji'

# Create a koji session
kojisession = koji.ClientSession('https://koji.fedoraproject.org/kojihub')

# Generate a list of packages to iterate over
pkgs = ['arprec', 'bcm283x-firmware', 'build-constraints-rpm-macros', 'CFR', 'chessx', 'cockpit-session-recording', 'console-image-viewer', 'container-exception-logger', 'container-storage-setup', 'convmv', 'cool-retro-term', 'copr-frontend', 'copr-selinux', 'corkscrew', 'corosync-qdevice', 'corrida', 'cortado', 'couchdb', 'courier-unicode', 'cowpatty', 'cowsay-beefymiracle', 'cowsay', 'coxeter', 'cp2k', 'cpdup', 'cpipe', 'cppcodec', 'cpphs', 'cppi', 'cppmyth', 'cpptest', 'cpptoml', 'cppunit', 'cppzmq', 'cproto', 'cptutils', 'cpuid', 'debootstrap', 'diffuse', 'dummy-test-package-gloster', 'elementary', 'gdesklets-goodweather', 'gnome-radio', 'golang-github-alecthomas-colour', 'gtk-gnutella', 'iaito', 'jbosscache-support', 'krb5', 'libdecor', 'libgnome-media-profiles', 'libsodium13', 'libunwind', 'libyang2', 'linuxptp', 'lxcfs', 'mcrouter', 'mcrypt', 'mcstrans', 'md5deep', 'mingw-curl', 'mock-centos-sig-configs', 'mysql++', 'octave-iso2mesh', 'openjfx', 'paintown', 'pam', 'perl-autodie', 'perl-bignum', 'perlbrew', 'perl-ccom', 'perl-constant-tiny', 'perl-criticism', 'perl-DBD-SQLite', 'perl-eperl', 'perl-experimental', 'perl-File-Touch', 'perl-gettext', 'perl-goto-file', 'perl-iCal-Parser', 'perl-inc-latest', 'perl-indirect', 'perl-lexical-underscore', 'perl-libnet', 'perl-libwhisker2', 'perl-libwww-perl', 'perl-libxml-perl', 'perl-mime-construct', 'perl-Net-LDAP-Server', 'perl-Net-Server', 'perl-parent', 'perl-perlfaq', 'perl-perlindex', 'perl-Pod-Coverage', 'perl-Pod-Eventual', 'perl-Pod-Parser', 'perl-Pod-Strip', 'perl-syntax', 'perl-Test-Stream', 'perl-threads-lite', 'perl-threads', 'perl-TimeDate', 'perl-Time-Mock', 'perl-Time-timegm', 'perl-Time-Warp', 'perl-Time-y2038', 'perl-Titanium', 'perl-Tk-Canvas-GradientColor', 'perl-Tk-ColoredButton', 'perl-Tk-CursorControl', 'perl-Tk-DoubleClick', 'perl-Tk-GraphViz', 'perl-Tk-Stderr', 'perl-Tk-TableMatrix', 'perl-Tk-Text-SuperText', 'perl-Tk-ToolBar', 'perl-Tree-DAG_Node', 'perl-Tree-R', 'perl-Tree-Simple-VisitorFactory', 'perl-Tree', 'perl-Tree-XPathEngine', 'perl-TryCatch', 'perl-Twiggy', 'perl-Types-DateTime', 'perl-Types-Path-Tiny', 'perl-Types-Serialiser', 'perl-Types-URI', 'perl-Types-UUID', 'perl-Type-Tie', 'perl-Type-Tiny', 'perl-Unicode-CaseFold', 'perl-Unicode-Casing', 'perl-Unicode-CheckUTF8', 'perl-Unicode-Collate', 'perl-Unicode-MapUTF8', 'perl-Unicode-Normalize', 'perl-Unicode-UTF8', 'perl-UNIVERSAL-can', 'perl-UNIVERSAL-exports', 'perl-UNIVERSAL-isa', 'perl-UNIVERSAL-moniker', 'perl-UNIVERSAL-ref', 'perl-UNIVERSAL-require', 'perl-Unix-Groups-FFI', 'perl-Unix-Mknod', 'perl-Unix-Process', 'perl-Unix-Statgrab', 'perl-Unix-Syslog', 'perl-URI-cpan', 'perl-URI-Encode', 'perl-URI-Escape-XS', 'perl-URI-Fetch', 'perl-URI-Find-Simple', 'perl-URI-Find', 'perl-URI-FromHash', 'perl-URI-NamespaceMap', 'perl-URI-Nested', 'perl-URI-Query', 'perl-URI-ws', 'perl-URL-Encode-XS', 'perl-User-Identity', 'perl-User', 'perl-User-Utmp', 'perl-UUID-URandom', 'perl-v6', 'perl-Validation-Class', 'perl-Variable-Magic', 'perl-Verilog-CodeGen', 'perl-Verilog-Perl', 'perl-Verilog-Readmem', 'perl-Version-Next', 'perl-version', 'perl-VM-EC2-Security-CredentialCache', 'perl-VM-EC2', 'perl-VMware-LabManager', 'perl-VOMS-Lite', 'perl-V', 'perl-Want', 'perl-Web-ID', 'perl-Web-Paste-Simple', 'perl-Web-Scraper', 'perl-WebService-Dropbox', 'perl-WebService-Linode', 'perl-WebService-MusicBrainz', 'perl-WebService-Rajce', 'perl-WebService-Validator-CSS-W3C', 'perl-Workflow', 'perl-WWW-Curl', 'perl-WWW-DuckDuckGo', 'perl-WWW-Form-UrlEncoded', 'perl-WWW-GoodData', 'perl-WWW-Mechanize-GZip', 'perl-WWW-Mechanize', 'perl-WWW-OrangeHRM-Client', 'perl-WWW-RobotRules', 'perl-WWW-Salesforce', 'perl-WWW-Search', 'perl-WWW-Shorten', 'perl-WWW-Splunk', 'perl-WWW-Twilio-API', 'perl-WWW-Twilio-TwiML', 'perl-WWW-xkcd', 'perl-Wx-GLCanvas', 'perl-Wx-Perl-ProcessStream', 'perl-Wx', 'perl-X10', 'perl-X11-Protocol-Other', 'perl-X11-Protocol', 'perl-XML-Atom-OWL', 'perl-XML-Atom-SimpleFeed', 'perl-XML-Atom', 'perl-XML-Bare', 'perl-XML-Catalog', 'perl-XML-CommonNS', 'perl-XML-DifferenceMarkup', 'perl-XML-DOM', 'perl-XML-DOM-XPath', 'perl-XML-DTDParser', 'perl-XML-Dumper', 'perl-XML-Entities', 'perl-XML-Fast', 'perl-XML-FeedPP', 'perl-XML-Feed', 'perl-XML-Filter-BufferText', 'perl-XML-Filter-XInclude', 'pesign-test-app', 'phpcov', 'phpcpd', 'phpdoc', 'php-doctrine-cache', 'php-doctrine-collections', 'php-doctrine-deprecations', 'php-horde-Horde-Image', 'php-horde-Horde-Injector', 'php-horde-Horde-Log', 'php-jsonlint', 'php-justinrainbow-json-schema5', 'php-khanamiryan-qrcode-detector-decoder', 'php-laminas-xml', 'phpMyAdmin', 'php-nikic-php-parser4', 'php-pdepend-PHP-Depend', 'php-pecl-couchbase3', 'php-phpmd-PHP-PMD', 'php-pimple1', 'php-react-child-process', 'php-react-http', 'php-sebastian-code-unit-reverse-lookup', 'php-sebastian-comparator4', 'php-sebastian-environment4', 'php-sebastian-environment5', 'php-sebastian-exporter3', 'php-sebastian-finder-facade2', 'php-sebastian-global-state2', 'php-sebastian-global-state3', 'php-sebastian-global-state4', 'php-sebastian-global-state5', 'php-sebastian-global-state', 'php-sebastian-lines-of-code', 'php-sebastian-object-enumerator3', 'php-sebastian-object-enumerator4', 'php-sebastian-object-enumerator', 'php-sebastian-object-reflector2', 'php-sebastian-object-reflector', 'php-sebastian-recursion-context3', 'php-sebastian-recursion-context4', 'php-sebastian-recursion-context', 'php-sebastian-resource-operations2', 'php-sebastian-resource-operations3', 'php-sebastian-resource-operations', 'php-sebastian-type2', 'php-sebastian-type', 'php-simplepie', 'php-symfony4', 'php-symfony-polyfill', 'php-symfony-security-acl', 'php-symfony', 'php-tcpdf', 'php-theseer-directoryscanner', 'php-theseer-tokenizer', 'php-true-punycode', 'php-twig2', 'php-twig3', 'php-twig', 'php-typo3-phar-stream-wrapper2', 'phpunit7', 'php-victorjonsson-markdowndocs', 'php-vlucas-phpdotenv', 'php-voms-admin', 'php-webflo-drupal-finder', 'php-webimpress-safe-writer', 'php-wikimedia-ip-set', 'php-wikimedia-utfnormal', 'php-zipstream', 'php-zmq', 'php-zordius-lightncandy', 'php-zstd', 'physfs', 'picard', 'picmi', 'picocli', 'picocom', 'picojson', 'pidgin-toobars', 'pidgin-window-merge', 'pim-sieve-editor', 'pinpoint', 'pkcs11-helper', 'pkgtreediff', 'planets', 'plank', 'plantumlqeditor', 'plantuml', 'plasma-applet-redshift-control', 'plasma-applet-translator', 'plasma-applet-weather-widget', 'plasma-breeze', 'plasma-browser-integration', 'plasma-desktop', 'plasma-firewall', 'plasma-integration', 'plasma-mediacenter', 'plasma-oxygen', 'plasma-pk-updates', 'plasma-systemsettings', 'plasma-thunderbolt', 'plasma-vault', 'plasma-wayland-protocols', 'plasma-widget-menubar', 'plasma-workspace', 'plasma-workspace-wallpapers', 'platform', 'playerctl', 'player', 'playitagainsam', 'plee-the-bear', 'plexus-active-collections', 'plexus-archiver', 'plexus-build-api', 'plexus-cipher', 'plexus-classworlds', 'plexus-compiler', 'plexus-component-api', 'plexus-components-pom', 'plexus-containers', 'plexus-languages', 'plexus-pom', 'pl', 'podofo', 'poedit', 'polkit-qt', 'postgresql-odbc', 'pragha', 'pre-commit', 'prename', 'python3-gssapi', 'python3-prctl', 'python-azure-common', 'python-azure-core', 'python-azure-cosmos', 'python-azure-datalake-store', 'python-azure-graphrbac', 'python-azure-identity', 'python-azure-keyvault', 'python-azure-mgmt-apimanagement', 'python-azure-mgmt-authorization', 'python-azure-mgmt-batchai', 'python-azure-mgmt-botservice', 'python-azure-mgmt-compute', 'python-azure-mgmt-consumption', 'python-azure-mgmt-containerinstance', 'python-azure-mgmt-containerregistry', 'python-azure-mgmt-core', 'python-azure-mgmt-databoxedge', 'python-azure-mgmt-datalake-analytics', 'python-azure-mgmt-datalake-store', 'python-azure-mgmt-deploymentmanager', 'python-azure-mgmt-devtestlabs', 'python-azure-mgmt-eventhub', 'python-azure-mgmt-iotcentral', 'python-azure-mgmt-kusto', 'python-azure-mgmt-managementgroups', 'python-azure-mgmt-media', 'python-azure-mgmt-msi', 'python-azure-mgmt-rdbms', 'python-azure-mgmt-recoveryservicesbackup', 'python-azure-mgmt-redhatopenshift', 'python-azure-mgmt-redis', 'python-azure-mgmt-relay', 'python-azure-mgmt-reservations', 'python-azure-mgmt-resource', 'python-azure-mgmt-security', 'python-azure-mgmt-servicefabric', 'python-azure-mgmt-sql', 'python-azure-mgmt-web', 'python-azure-storage-common', 'python-azure-synapse-accesscontrol', 'python-azure-synapse-artifacts', 'python-azure-synapse-spark', 'python-catkin_pkg', 'python-certbot-dns-nsone', 'python-charset-normalizer', 'python-chirpstack-api', 'python-colcon-parallel-executor', 'python-colorspacious', 'python-colorzero', 'python-colour-runner', 'python-configargparse', 'python-confluent-kafka', 'python-confuse', 'python-connect-box', 'python-connection_pool', 'python-cooldict', 'python-copr-common', 'python-cornice', 'python-coverage_pth', 'python-coverage', 'python-coveralls', 'python-daemonize', 'python-daemon', 'python-daikin', 'python-daiquiri', 'python-danfossair', 'python-daphne', 'python-datadog', 'python-datanommer-consumer', 'python-datanommer-models', 'python-dbfread', 'python-dbus-client-gen', 'python-dbusmock', 'python-dbus-python-client-gen', 'python-dbus-signature-pyparsing', 'python-dbutils', 'python-ddt', 'python-debianbts', 'python-debtcollector', 'python-deconz', 'python-decopatch', 'python-decorator', 'python-deepdiff', 'python-defcon', 'python-defusedxml', 'python-demjson', 'python-designateclient', 'python-devolo-home-control-api', 'python-dialog', 'python-dictdiffer', 'python-dictdumper', 'python-didl-lite', 'python-diff-cover', 'python-diff-match-patch', 'python-digitalocean', 'python-dijitso', 'python-dill', 'python-dingz', 'python-dipy', 'python-dirq', 'python-discord', 'python-diskcache', 'python-distlib', 'python-distutils-extra', 'python-django-ajax-selects', 'python-django-annoying', 'python-django-appconf', 'python-django-auth-ldap', 'python-django-configurations', 'python-django-contact-form', 'python-django-contrib-comments', 'python-django-cors-headers', 'python-django-crispy-forms', 'python-django-database-url', 'python-django-debreach', 'python-django-debug-toolbar', 'python-django-filter', 'python-django-formtools', 'python-django-haystack', 'python-django-ipware', 'python-django-macros', 'python-django-markdownx', 'python-django-nose', 'python-django-pglocks', 'python-django-pipeline', 'python-django-post_office', 'python-django-prometheus', 'python-djangoql', 'python-django-redis', 'python-django-rest-framework', 'python-django', 'python-django-taggit-serializer', 'python-dmidecode', 'python-dns', 'python-dockerfile-parse', 'python-dockerpty', 'python-docker-pycreds', 'python-docker-squash', 'python-docopt', 'python-docs-theme', 'python-docutils', 'python-docx', 'python-dogpile-cache', 'python-doit', 'python-doubleratchet', 'python-doxytag2zealdb', 'python-dpkt', 'python-drat', 'python-drgn', 'python-dropbox', 'python-dtfabric', 'python-dtopt', 'python-duecredit', 'python-dukpy', 'python-dulwich', 'python-earthpy', 'python-easyargs', 'python-easyco', 'python-easygui', 'python-eccodes', 'python-ecdsa', 'python-editdistance', 'python-editdistance-s', 'python-editorconfig', 'python-editor', 'python-elementpath', 'python-elpy', 'python-email_reply_parser', 'python-emoji', 'python-empy', 'python-enchant', 'python-enlighten', 'python-enrich', 'python-enthought-sphinx-theme', 'python-entrypoints', 'python-envisage', 'python-enzyme', 'python-epc', 'python-epel-rpm-macros', 'python-ephem', 'python-epi', 'python-epub', 'python-etcd3gw', 'python-etcd3', 'python-ethtool', 'python-et_xmlfile', 'python-evdev', 'python-eventlet', 'python-events', 'python-evic', 'python-execnet', 'python-exif', 'python-extension-helpers', 'python-extras', 'python-eyed3', 'python-f5-sdk', 'python-fabric', 'python-factory-boy', 'python-faker', 'python-falcon', 'python-fasjson-client', 'python-fastavro', 'python-fasteners', 'python-fastimport', 'python-fastjsonschema', 'python-fastprogress', 'python-fastpurge', 'python-fauxquests', 'python-fb-re2', 'python-fdb', 'python-feedgenerator', 'python-feedparser', 'python-fiat', 'python-fido2', 'python-fields', 'python-filecheck', 'python-filelock', 'python-filetype', 'python-fiona', 'python-firkin', 'python-fitsio', 'python-fixit', 'python-fixtures', 'python-flake8-docstrings', 'python-flake8-import-order', 'python-flask-login', 'python-flask-mako', 'python-flask-multistatic', 'python-flask-oidc', 'python-flask-openid', 'python-flask-restplus', 'python-flask-sqlalchemy', 'python-flask-talisman', 'python-flask-whooshee', 'python-flask-wtf-decorators', 'python-flask-xml-rpc', 'python-flexmock', 'python-flit', 'python-flock', 'python-flufl-bounce', 'python-fluidity-sm', 'python-fontconfig', 'python-fontMath', 'python-fontname', 'python-formats', 'python-fpylll', 'python-fqdn', 'python-freeipa', 'python-freezegun', 'python-friendlyloris', 'python-fs', 'python-google-cloud-iam', 'python-h2', 'python-hypothesis', 'python-imbalanced-learn', 'python-jaraco-text', 'python-javabridge', 'python-javaproperties', 'python-jedi', 'python-jellyfish', 'python-jinja2-cli', 'python-jinja2_pluralize', 'python-jinja2-time', 'python-jira', 'python-jsmin', 'python-kerberos', 'python-krbcontext', 'python-kubernetes', 'python-launchpadlib', 'python-libarchive-c', 'python-libevdev', 'python-mpd', 'python-octaviaclient', 'python-pelican', 'python-pyarlo', 'python-pyasn1', 'python-pycparser', 'python-pyfastnoisesimd', 'python-pyqtgraph', 'python-pyramid_sawing', 'python-pytelegrambotapi', 'python-satyr', 'python-shellingham', 'python-supersmoother', 'python-sybil', 'python-tasklib', 'python-tasmotadevicecontroller', 'python-threadpoolctl', 'python-timeout-decorator', 'python-timeunit', 'python-tinycss2', 'python-tinydb', 'python-tinyrpc', 'python-tld', 'python-toml-adapt', 'python-tomlkit', 'python-toml', 'python-toolz', 'python-tosca-parser', 'python-tox-current-env', 'python-tqdm', 'python-transaction', 'python-transforms3d', 'python-translationstring', 'python-translitcodec', 'python-treq', 'python-trimesh', 'python-trio', 'python-trollius', 'python-trololio', 'python-troveclient', 'python-trustme', 'python-ttystatus', 'python-tubes', 'python-tvb-data', 'python-tw2-core', 'python-tw2-forms', 'python-twiggy', 'python-twine', 'python-twisted', 'python-twitter', 'python-txaio', 'python-txredisapi', 'python-txtorcon', 'python-txws', 'python-txzmq', 'python-typedecorator', 'python-typeguard', 'python-typeshed', 'python-typogrify', 'python-tzlocal', 'python-uamqp', 'python-ufoLib2', 'python-ujson', 'python-u-msgpack-python', 'python-unidecode', 'python-unidiff', 'python-unipath', 'python-upnpy', 'python-upoints', 'python-upt-cpan', 'python-uranium', 'python-uritemplate', 'python-uri-templates', 'python-utmp', 'python-varlink', 'python-vcstool', 'python-vcstools', 'python-vdf', 'python-velbus', 'python-venusian', 'python-verboselogs', 'python-versioneer', 'python-versiontools', 'python-vevents', 'python-vine', 'python-virtualbmc', 'python-virtualenv-api', 'python-virtualenv-clone', 'python-virtualenv', 'python-visionegg-quest', 'python-visitor', 'python-visvis', 'python-vitrageclient', 'python-vobject', 'python-volatile', 'python-volkszaehler', 'python-voluptuous-serialize', 'python-voluptuous', 'python-vsts', 'python-walkdir', 'python-waqiasync', 'python-warlock', 'python-watchdog', 'python-watchgod', 'python-waterfurnace', 'python-wavio', 'python-wcmatch', 'python-wcwidth', 'python-webcolors', 'python-webob', 'python-websocket-client', 'python-websockets', 'python-webtest', 'python-webthing-ws', 'python-wheel', 'python-whois', 'python-widgetsnbextension', 'python-winrm', 'python-wled', 'python-wloc', 'python-wrapt', 'python-ws4py', 'python-wsaccel', 'python-wsgi_intercept', 'python-wtforms', 'python-wtf-peewee', 'python-wurlitzer', 'python-www-authenticate', 'python-wxnatpy', 'python-wxpython4', 'python-x2go', 'python-x3dh', 'python-xapp', 'python-xarray', 'python-xbout', 'python-xboxapi', 'python-xcffib', 'python-xdot', 'python-xeddsa', 'python-xlib', 'python-yamlordereddictloader', 'python-zope-sqlalchemy', 'python-zope-testing', 'python-zope-testrunner', 'python-zstandard', 'pywbem', 'qcad', 'qcint', 'qstat', 'qtpass', 'redis', 'rubygem-boxgrinder-build', 'rubygem-boxgrinder-core', 'rubygem-bson', 'rubygem-bundler_ext', 'rubygem-dnsruby', 'rubygem-docile', 'rubygem-escape', 'rubygem-fog-core', 'rubygem-fog-xml', 'rubygem-gem-nice-install', 'rubygem-hashery', 'rubygem-hiredis', 'rubygem-hrx', 'rubygem-http_connection', 'rubygem-idn', 'rubygem-image_processing', 'rubygem-jekyll', 'rubygem-launchy', 'rubygem-linked-list', 'rubygem-liquid', 'rubygem-listen', 'rubygem-little-plugger', 'rubygem-lockfile', 'rubygem-lumberjack', 'rubygem-macaddr', 'rubygem-mail', 'rubygem-marcel', 'rubygem-memcache-client', 'rubygem-metaclass', 'rubygem-mimemagic', 'rubygem-mime-types-data', 'rubygem-mini_magick', 'rubygem-minima', 'rubygem-mini_mime', 'rubygem-minitest-around', 'rubygem-minitest', 'rubygem-mizuho', 'rubygem-more_core_extensions', 'rubygem-morph-cli', 'rubygem-public_suffix', 'rubygem-rack-restful_submit', 'rust-cookie', 'rust-crossbeam-epoch0.8', 'rust-curl-sys', 'rust-cursive', 'rust-cxx', 'rust-dbus0.8', 'rust-dbus-tokio', 'rust-dbus-tree', 'rust-defmac', 'rust-delta_e', 'rust-derivative', 'rust-derive_arbitrary0.4', 'rust-derive_builder0.9', 'rust-derive_builder_core0.9', 'rust-derive_builder_core', 'rust-derive_builder_macro', 'rust-derive_builder', 'rust-derive-new', 'rust-desed', 'rust-des', 'rust-diesel_derives', 'rust-diffus-derive', 'rust-diffus', 'rust-dirs2', 'rust-dlib0.4', 'rust-dlv-list', 'rust-dotenv', 'rust-downcast-rs', 'rust-dtoa-short', 'rust-dtoa', 'rust-dua-cli', 'rust-duct', 'rust-dummy', 'rust-dutree', 'rust-ena', 'rust-encode_unicode', 'rust-encoding_index_tests', 'rust-encoding_rs_io', 'rust-encoding_rs', 'rust-endian-type', 'rust-entities', 'rust-enum-as-inner', 'rust-enum-iterator-derive', 'rust-enum-iterator', 'rust-enumset_derive', 'rust-environment', 'rust-env_logger0.4', 'rust-env_logger0.5', 'rust-env_logger0.6', 'rust-env_logger0.7', 'rust-env_logger', 'rust-epoll', 'rust-erased-serde', 'rust-errno', 'rust-error-chain', 'rust-escaper', 'rust-escargot', 'rust-euclid', 'rust-extend', 'rust-extprim_literals_macros', 'rust-extprim', 'rust-fail', 'rust-failure_derive', 'rust-failure', 'rust-failure-tools', 'rust-fake_clock', 'rust-fake-simd', 'rust-fake', 'rust-fallible-iterator', 'rust-fastrand', 'rust-fb_procfs', 'rust-fbthrift_codegen_includer_proc_macro', 'rust-fd-lock', 'rust-fedora-coreos-pinger', 'rust-fedora', 'rust-fedora-update-feedback', 'rust-feedbin_api', 'rust-feedly_api', 'rust-femme', 'rust-fern', 'rust-fever_api', 'rust-ffsend', 'rust-filedescriptor', 'rust-fn-error-context', 'rust-foreign-types-macros', 'rust-foreign-types-shared0.1', 'rust-foreign-types-shared', 'rust-foreign-types', 'rust-form_urlencoded', 'rust-freetype-rs', 'rust-freetype-sys', 'rust-fs2', 'rust-fs_extra', 'rust-fs-set-times', 'rust-futf', 'rust-futures0.1', 'rust-futures-channel', 'rust-futures-core', 'rust-futures-cpupool', 'rust-futures-executor', 'rust-futures-io', 'rust-futures-lite', 'rust-futures-macro', 'rust-futures', 'rust-futures-test', 'rust-futures-timer', 'rust-futures-util', 'rust-fuzzy-matcher', 'rust-fxhash', 'rust-gcsf', 'rust-gdk-pixbuf-sys', 'rust-gdk', 'rust-generic-array', 'rust-getch', 'rust-gethostname', 'rust-getopts', 'rust-getrandom0.1', 'rust-getset', 'rust-gettext-rs', 'rust-gettext-sys', 'rust-ghash', 'rust-ghost', 'rust-gif', 'rust-gio', 'rust-gir-format-check', 'rust-git2-curl', 'rust-git2', 'rust-git-delta', 'rust-glib-sys', 'rust-glob', 'rust-globwalk', 'rust-glutin', 'rust-gobject-sys', 'rust-goblin', 'rust-google-drive3-fork', 'rust-gptman', 'rust-grep-cli', 'rust-grep-matcher', 'rust-grep-pcre2', 'rust-grep-printer', 'rust-grep-regex', 'rust-grep-searcher', 'rust-grep', 'rust-gspell', 'rust-gspell-sys', 'rust-gstreamer-audio', 'rust-gstreamer-pbutils', 'rust-gstreamer-player', 'rust-gstreamer', 'rust-gstreamer-sys', 'rust-gstreamer-video', 'rust-gzip-header', 'rust-h2_0.2', 'rust-h2', 'rust-hamcrest2', 'rust-hamcrest', 'rust-handlebars', 'rust-hashbrown', 'rust-hashlink', 'rust-headers-core', 'rust-headers-derive', 'rust-headers', 'rust-heapsize', 'rust-heatseeker', 'rust-heck', 'rust-hex-literal0.2', 'rust-hex-literal-impl', 'rust-hex-literal', 'rust-hex', 'rust-hkdf', 'rust-hmac', 'rust-html2pango', 'rust-http', 'rust-human-sort', 'rust-hyper0.10', 'rust-hyper0.13', 'rust-hyperfine', 'rust-hyper-native-tls', 'rust-hyper-rustls', 'rust-hyper-staticfile', 'rust-hyper-tls0.4', 'rust-hyper-tls', 'rust-i3ipc', 'rust-idna0.1', 'rust-idna', 'rust-id_tree', 'rust-ignore', 'rust-image', 'rust-im-rc', 'rust-indexmap', 'rust-indicatif', 'rust-indoc', 'rust-inflate', 'rust-inotify', 'rust-inotify-sys', 'rust-itertools0.8', 'rust-itoa', 'rust-libloading0.6', 'rust-libloading', 'rust-nom5', 'rust-noop_proc_macro', 'rust-normalize-line-endings', 'rust-notify', 'rust-parking_lot_core', 'rust-parsec-client', 'rust-parse_cfg', 'rust-parsec-interface', 'rust-parse-zoneinfo', 'rust-partial-io', 'rust-pin-project-internal0.4', 'rust-png', 'rust-podio', 'rust-polling', 'rust-pom', 'rust-quick-error1', 'rust-quick-error', 'rust-ripgrep', 'rust-ruma-identifiers-macros', 'rust-rustc-serialize', 'rust-rustc-test', 'rust-rustc_tools_util', 'rust-scheduled-thread-pool', 'rust-scoped_threadpool', 'rust-scoped-tls-hkt', 'rust-scoped-tls', 'rust-sequoia-keyring-linter', 'rust-serde_test', 'rust-serde_urlencoded0.6', 'rust-serde_url_params', 'rust-serde_with_macros', 'rust-serde_yaml', 'rust-serial-core', 'rust-sluice', 'rust-smallstr', 'rust-structopt0.2', 'rust-strum', 'rust-sysinfo', 'rust-threadpool', 'rust-tokio-udp', 'rust-tokio-uds', 'rust-tokio-util0.2', 'rust-tokio-util', 'rust-try_from', 'rust-try-lock', 'rust-typenum', 'rust-typetag-impl', 'rust-typetag', 'rust-ucd-trie', 'rust-varlink-cli', 'rust-varlink_generator', 'rust-varlink_parser', 'rust-webkit2gtk', 'rust-webkit2gtk-sys', 'rust-webpki-roots', 'rust-webpki', 'saab-fonts', 'samplv1', 'sane-backends', 'sblim-cmpi-fsvol', 'seamonkey', 'spatialite-gui', 'squashfs-tools', 'sscg', 'stalld', 'sympa', 'systemd', 'tcl', 'tuned', 'uboot-tools', 'udunits', 'ulauncher', 'vconfig', 'vcsh', 'vdirsyncer', 'vdpauinfo', 'vdr-epg-daemon', 'vdr', 'wine', 'xtv', 'zram']

print('Checking %s packages...' % len(pkgs))

# Loop over each package
for pkg in pkgs:
    name = pkg
    id = kojisession.getPackageID(name)

    # some package we just dont want to ever rebuild
    if name in massrebuild['pkg_skip_list']:
        print('Skipping %s, package is explicitely skipped')
        continue

    # Query to see if a build has already successfully completed
    # state = 1 is successfully completed builds
    builds = kojisession.listBuilds(id, completeAfter=massrebuild['epoch'], state=1)
    newbuild = False
    # Check the builds to make sure they were for the target we care about
    for build in builds:
        try:
            buildtarget = kojisession.getTaskInfo(build['task_id'],
                                       request=True)['request'][1]
            if buildtarget == massrebuild['target'] or buildtarget in massrebuild['targets']:
                # We've already got an attempt made, skip.
                newbuild = True
                break
        except:
            print('Skipping %s, no taskinfo.' % name)
            continue
    if newbuild:
        print('Skipping %s, already attempted.' % name)
        continue

    # Check out git
    fedpkgcmd = ['fedpkg', '--user', 'releng', 'clone', '--branch', 'rawhide', name]
    print('Checking out %s' % name)
    if runme(fedpkgcmd, 'fedpkg', name, enviro):
        continue

    # Check for a checkout
    if not os.path.exists(os.path.join(workdir, name)):
        sys.stderr.write('%s failed checkout.\n' % name)
        continue

    # Check for a noautobuild file
    if os.path.exists(os.path.join(workdir, name, 'noautobuild')):
        # Maintainer does not want us to auto build.
        print('Skipping %s due to opt-out' % name)
        continue

    # Find the spec file
    files = os.listdir(os.path.join(workdir, name))
    spec = ''
    for file in files:
        if file.endswith('.spec'):
            spec = os.path.join(workdir, name, file)
            break

    if not spec:
        sys.stderr.write('%s failed spec check\n' % name)
        continue

    # rpmdev-bumpspec
    bumpspec = ['rpmdev-bumpspec', '-u', user, '-c', comment,
                os.path.join(workdir, name, spec)]
    print('Bumping %s' % spec)
    if runme(bumpspec, 'bumpspec', name, enviro):
        continue

    # Set the git user.name and user.email
    set_name = ['git', 'config', 'user.name', 'Fedora Release Engineering']
    set_mail = ['git', 'config', 'user.email', 'releng@fedoraproject.org']
    print('Setting git user.name and user.email')
    if runme(set_name, 'set_name', name, enviro,
                 cwd=os.path.join(workdir, name)):
        continue
    if runme(set_mail, 'set_mail', name, enviro,
                 cwd=os.path.join(workdir, name)):
        continue

    # git commit
    commit = ['git', 'commit', '-a', '-m', comment, '--allow-empty']
    print('Committing changes for %s' % name)
    if runme(commit, 'commit', name, enviro,
                 cwd=os.path.join(workdir, name)):
        continue

    # git push
    push = ['git', 'push', '--no-verify']
    print('Pushing changes for %s' % name)
    if runme(push, 'push', name, enviro,
                 cwd=os.path.join(workdir, name)):
        continue

    # get git url
    urlcmd = ['fedpkg', 'giturl']
    print('Getting git url for %s' % name)
    url = runmeoutput(urlcmd, 'giturl', name, enviro,
                 cwd=os.path.join(workdir, name))
    if not url:
        continue

    # build
    build = [koji_bin, 'build', '--nowait', '--background', '--fail-fast', massrebuild['target'], url]
    print('Building %s' % name)
    runme(build, 'build', name, enviro, 
          cwd=os.path.join(workdir, name))
