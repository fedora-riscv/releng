#!/usr/bin/python -tt
# vim: fileencoding=utf8


PKG_SKIP_LIST = [
    'fedora-modular-release',
    'fedora-modular-repos',
    'fedora-release',
    'fedora-repos',
    'generic-release',
    'glibc32',
    'grub2',
    'kernel',
    'linux-firmware',
    'openh264',
    'redhat-rpm-config',
    'shim',
    'shim-signed',
    'shim-unsigned-aarch64',
    'shim-unsigned-x64',
    'ghc',
    'ghc-rpm-macros',
    'ghc8.10',
    'ghc9.0',
    'ghc9.2',
    'ghc9.4',
    'haskell-platform',
    'Agda',
    'ShellCheck',
    'alex',
    'bench',
    'brainfuck',
    'bustle',
    'cab',
    'cabal-install',
    'cabal-rpm',
    'cpphs',
    'darcs',
    'dhall',
    'dhall-json',
    'dl-fedora',
    'fbrnch',
    'ghc-Boolean',
    'ghc-ConfigFile',
    'ghc-DAV',
    'ghc-Decimal',
    'ghc-Diff',
    'ghc-GLURaw',
    'ghc-Glob',
    'ghc-HSH',
    'ghc-HStringTemplate',
    'ghc-HTTP',
    'ghc-HUnit',
    'ghc-HaXml',
    'ghc-HsOpenSSL',
    'ghc-HsOpenSSL-x509-system',
    'ghc-HsYAML',
    'ghc-IOSpec',
    'ghc-IfElse',
    'ghc-JuicyPixels',
    'ghc-MemoTrie',
    'ghc-MissingH',
    'ghc-MonadCatchIO-mtl',
    'ghc-MonadCatchIO-transformers',
    'ghc-MonadRandom',
    'ghc-NumInstances',
    'ghc-ObjectName',
    'ghc-Only',
    'ghc-OpenGL',
    'ghc-OpenGLRaw',
    'ghc-QuickCheck',
    'ghc-RSA',
    'ghc-SHA',
    'ghc-STMonadTrans',
    'ghc-SafeSemaphore',
    'ghc-StateVar',
    'ghc-Stream',
    'ghc-X11',
    'ghc-X11-xft',
    'ghc-abstract-deque',
    'ghc-abstract-par',
    'ghc-adjunctions',
    'ghc-aeson',
    'ghc-aeson-better-errors',
    'ghc-aeson-compat',
    'ghc-aeson-pretty',
    'ghc-aeson-yaml',
    'ghc-annotated-wl-pprint',
    'ghc-ansi-terminal',
    'ghc-ansi-wl-pprint',
    'ghc-appar',
    'ghc-arrows',
    'ghc-asn1-encoding',
    'ghc-asn1-parse',
    'ghc-asn1-types',
    'ghc-assoc',
    'ghc-async',
    'ghc-atomic-write',
    'ghc-attoparsec',
    'ghc-attoparsec-binary',
    'ghc-attoparsec-iso8601',
    'ghc-authenticate-oauth',
    'ghc-auto-update',
    'ghc-aws',
    'ghc-base-compat',
    'ghc-base-compat-batteries',
    'ghc-base-orphans',
    'ghc-base-prelude',
    'ghc-base-unicode-symbols',
    'ghc-base16-bytestring',
    'ghc-base64-bytestring',
    'ghc-basement',
    'ghc-basic-prelude',
    'ghc-bencode',
    'ghc-bifunctors',
    'ghc-binary-shared',
    'ghc-bindings-DSL',
    'ghc-bitarray',
    'ghc-blaze-builder',
    'ghc-blaze-html',
    'ghc-blaze-markup',
    'ghc-blaze-textual',
    'ghc-bloomfilter',
    'ghc-bower-json',
    'ghc-boxes',
    'ghc-brick',
    'ghc-bsb-http-chunked',
    'ghc-bugzilla-redhat',
    'ghc-byteable',
    'ghc-byteorder',
    'ghc-bytes',
    'ghc-bytestring-nums',
    'ghc-bytestring-show',
    'ghc-bytestring-trie',
    'ghc-cabal-doctest',
    'ghc-cabal-file-th',
    'ghc-cabal-helper',
    'ghc-cairo',
    'ghc-call-stack',
    'ghc-case-insensitive',
    'ghc-cassava',
    'ghc-cautious-file',
    'ghc-cborg',
    'ghc-cborg-json',
    'ghc-cereal',
    'ghc-charset',
    'ghc-cheapskate',
    'ghc-chunked-data',
    'ghc-cipher-aes',
    'ghc-clientsession',
    'ghc-clock',
    'ghc-cmark',
    'ghc-cmark-gfm',
    'ghc-cmdargs',
    'ghc-code-page',
    'ghc-colour',
    'ghc-colourista',
    'ghc-comonad',
    'ghc-concatenative',
    'ghc-concurrent-extra',
    'ghc-concurrent-output',
    'ghc-cond',
    'ghc-conduit',
    'ghc-conduit-extra',
    'ghc-config-ini',
    'ghc-connection',
    'ghc-contravariant',
    'ghc-control-monad-free',
    'ghc-cookie',
    'ghc-cprng-aes',
    'ghc-criterion',
    'ghc-crypto-api',
    'ghc-crypto-cipher-types',
    'ghc-crypto-pubkey-types',
    'ghc-crypto-random',
    'ghc-cryptohash',
    'ghc-cryptohash-md5',
    'ghc-cryptohash-sha1',
    'ghc-cryptohash-sha256',
    'ghc-cryptonite',
    'ghc-cryptonite-conduit',
    'ghc-css-text',
    'ghc-csv',
    'ghc-curl',
    'ghc-data-accessor',
    'ghc-data-binary-ieee754',
    'ghc-data-clist',
    'ghc-data-default',
    'ghc-data-default-class',
    'ghc-data-default-instances-containers',
    'ghc-data-default-instances-dlist',
    'ghc-data-default-instances-old-locale',
    'ghc-data-fix',
    'ghc-data-hash',
    'ghc-data-inttrie',
    'ghc-data-memocombinators',
    'ghc-data-reify',
    'ghc-dataenc',
    'ghc-date-cache',
    'ghc-dbus',
    'ghc-dec',
    'ghc-deepseq-generics',
    'ghc-digest',
    'ghc-disk-free-space',
    'ghc-distributive',
    'ghc-djinn-ghc',
    'ghc-djinn-lib',
    'ghc-dlist',
    'ghc-dns',
    'ghc-doctemplates',
    'ghc-doctest',
    'ghc-dotgen',
    'ghc-double-conversion',
    'ghc-echo',
    'ghc-ed25519',
    'ghc-edit-distance',
    'ghc-either',
    'ghc-email-validate',
    'ghc-enclosed-exceptions',
    'ghc-entropy',
    'ghc-equivalence',
    'ghc-erf',
    'ghc-esqueleto',
    'ghc-executable-path',
    'ghc-explicit-exception',
    'ghc-extensible-exceptions',
    'ghc-extra',
    'ghc-fast-logger',
    'ghc-fclabels',
    'ghc-fdo-notify',
    'ghc-feed',
    'ghc-fgl',
    'ghc-file-embed',
    'ghc-filemanip',
    'ghc-filepath-bytestring',
    'ghc-filepattern',
    'ghc-filestore',
    'ghc-filtrable',
    'ghc-fingertree',
    'ghc-fixed',
    'ghc-foldl',
    'ghc-formatting',
    'ghc-foundation',
    'ghc-free',
    'ghc-fsnotify',
    'ghc-generic-deriving',
    'ghc-generics-sop',
    'ghc-ghc-lib-parser',
    'ghc-ghc-mtl',
    'ghc-ghc-paths',
    'ghc-ghc-syb-utils',
    'ghc-gi-atk',
    'ghc-gi-cairo',
    'ghc-gi-gdk',
    'ghc-gi-gdkpixbuf',
    'ghc-gi-gio',
    'ghc-gi-glib',
    'ghc-gi-gmodule',
    'ghc-gi-gobject',
    'ghc-gi-gtk',
    'ghc-gi-harfbuzz',
    'ghc-gi-ostree',
    'ghc-gi-pango',
    'ghc-gio',
    'ghc-git-lfs',
    'ghc-gitrev',
    'ghc-glib',
    'ghc-graphviz',
    'ghc-gtk',
    'ghc-gtk3',
    'ghc-hackage-security',
    'ghc-haddock-library',
    'ghc-hakyll',
    'ghc-half',
    'ghc-happstack-server',
    'ghc-hashable',
    'ghc-hashtables',
    'ghc-haskell-gi',
    'ghc-haskell-gi-base',
    'ghc-haskell-gi-overloading',
    'ghc-haskell-lexer',
    'ghc-haskell-src-exts',
    'ghc-haskell-src-exts-util',
    'ghc-haskell-src-meta',
    'ghc-haxr',
    'ghc-hgettext',
    'ghc-highlighting-kate',
    'ghc-hinotify',
    'ghc-hint',
    'ghc-hjsmin',
    'ghc-hledger-lib',
    'ghc-hoauth2',
    'ghc-hosc',
    'ghc-hostname',
    'ghc-hourglass',
    'ghc-hs-bibutils',
    'ghc-hslogger',
    'ghc-hslua',
    'ghc-hslua-module-text',
    'ghc-hspec',
    'ghc-hspec-core',
    'ghc-hspec-discover',
    'ghc-hspec-expectations',
    'ghc-hspec-megaparsec',
    'ghc-html',
    'ghc-html-conduit',
    'ghc-htoml',
    'ghc-http-api-data',
    'ghc-http-client',
    'ghc-http-client-openssl',
    'ghc-http-client-restricted',
    'ghc-http-client-tls',
    'ghc-http-common',
    'ghc-http-conduit',
    'ghc-http-date',
    'ghc-http-directory',
    'ghc-http-media',
    'ghc-http-query',
    'ghc-http-streams',
    'ghc-http-types',
    'ghc-http2',
    'ghc-hxt',
    'ghc-hxt-charproperties',
    'ghc-hxt-regex-xmlschema',
    'ghc-hxt-unicode',
    'ghc-ieee754',
    'ghc-ilist',
    'ghc-indents',
    'ghc-indexed-traversable',
    'ghc-infer-license',
    'ghc-integer-logarithms',
    'ghc-io-streams',
    'ghc-iproute',
    'ghc-iso8601-time',
    'ghc-js-flot',
    'ghc-js-jquery',
    'ghc-json',
    'ghc-kan-extensions',
    'ghc-koji',
    'ghc-language-c',
    'ghc-language-docker',
    'ghc-language-ecmascript',
    'ghc-language-java',
    'ghc-language-javascript',
    'ghc-lazysmallcheck',
    'ghc-lens',
    'ghc-lens-aeson',
    'ghc-lens-family-core',
    'ghc-libffi',
    'ghc-libmpd',
    'ghc-libxml-sax',
    'ghc-lifted-base',
    'ghc-listsafe',
    'ghc-logging-facade',
    'ghc-logict',
    'ghc-lrucache',
    'ghc-lukko',
    'ghc-lzma-conduit',
    'ghc-maccatcher',
    'ghc-magic',
    'ghc-managed',
    'ghc-math-functions',
    'ghc-megaparsec',
    'ghc-memory',
    'ghc-microlens',
    'ghc-microlens-ghc',
    'ghc-microlens-mtl',
    'ghc-microlens-platform',
    'ghc-microlens-th',
    'ghc-microstache',
    'ghc-mime-types',
    'ghc-mmap',
    'ghc-mmorph',
    'ghc-mockery',
    'ghc-modern-uri',
    'ghc-monad-control',
    'ghc-monad-journal',
    'ghc-monad-logger',
    'ghc-monad-loops',
    'ghc-monad-par',
    'ghc-monad-par-extras',
    'ghc-monads-tf',
    'ghc-mono-traversable',
    'ghc-mountpoints',
    'ghc-mtlparse',
    'ghc-mwc-random',
    'ghc-nanospec',
    'ghc-natural-transformation',
    'ghc-netlist',
    'ghc-netlist-to-vhdl',
    'ghc-network',
    'ghc-network-bsd',
    'ghc-network-byte-order',
    'ghc-network-info',
    'ghc-network-multicast',
    'ghc-network-uri',
    'ghc-numbers',
    'ghc-oeis',
    'ghc-old-locale',
    'ghc-old-time',
    'ghc-openssl-streams',
    'ghc-optional-args',
    'ghc-optparse-applicative',
    'ghc-optparse-simple',
    'ghc-pandoc-types',
    'ghc-pango',
    'ghc-parallel',
    'ghc-parsec-numbers',
    'ghc-parser-combinators',
    'ghc-parsers',
    'ghc-path',
    'ghc-path-io',
    'ghc-path-pieces',
    'ghc-pattern-arrows',
    'ghc-pcap',
    'ghc-pcre-light',
    'ghc-pem',
    'ghc-persistent',
    'ghc-persistent-sqlite',
    'ghc-persistent-template',
    'ghc-pipes',
    'ghc-polyparse',
    'ghc-prelude-extras',
    'ghc-pretty-show',
    'ghc-pretty-simple',
    'ghc-pretty-terminal',
    'ghc-prettyprinter',
    'ghc-prettyprinter-ansi-terminal',
    'ghc-primitive',
    'ghc-profunctors',
    'ghc-protolude',
    'ghc-psqueues',
    'ghc-publicsuffixlist',
    'ghc-pureMD5',
    'ghc-quickcheck-io',
    'ghc-random',
    'ghc-ranges',
    'ghc-readline',
    'ghc-recaptcha',
    'ghc-reducers',
    'ghc-refact',
    'ghc-reflection',
    'ghc-regex-applicative',
    'ghc-regex-base',
    'ghc-regex-compat',
    'ghc-regex-pcre',
    'ghc-regex-posix',
    'ghc-regex-tdfa',
    'ghc-regexpr',
    'ghc-relude',
    'ghc-repline',
    'ghc-req',
    'ghc-resolv',
    'ghc-resource-pool',
    'ghc-resourcet',
    'ghc-retry',
    'ghc-rfc5051',
    'ghc-rio',
    'ghc-rio-prettyprint',
    'ghc-rosezipper',
    'ghc-rpm-nvr',
    'ghc-safe',
    'ghc-sandi',
    'ghc-scientific',
    'ghc-scotty',
    'ghc-securemem',
    'ghc-semigroupoids',
    'ghc-semigroups',
    'ghc-semver',
    'ghc-sendfile',
    'ghc-serialise',
    'ghc-servant',
    'ghc-servant-client',
    'ghc-servant-client-core',
    'ghc-servant-foreign',
    'ghc-servant-options',
    'ghc-servant-server',
    'ghc-setenv',
    'ghc-setlocale',
    'ghc-shakespeare',
    'ghc-shelly',
    'ghc-show',
    'ghc-silently',
    'ghc-simple-cabal',
    'ghc-simple-cmd',
    'ghc-simple-cmd-args',
    'ghc-simple-sendfile',
    'ghc-singleton-bool',
    'ghc-skein',
    'ghc-skylighting',
    'ghc-smallcheck',
    'ghc-snap-core',
    'ghc-snap-server',
    'ghc-socks',
    'ghc-sourcemap',
    'ghc-spdx',
    'ghc-split',
    'ghc-statistics',
    'ghc-stm-chans',
    'ghc-streaming-commons',
    'ghc-strict',
    'ghc-string-conversions',
    'ghc-string-qq',
    'ghc-stringbuilder',
    'ghc-stringsearch',
    'ghc-syb',
    'ghc-system-fileio',
    'ghc-system-filepath',
    'ghc-tabular',
    'ghc-tagged',
    'ghc-tagsoup',
    'ghc-tar',
    'ghc-tar-conduit',
    'ghc-tasty',
    'ghc-tasty-hunit',
    'ghc-tasty-kat',
    'ghc-tasty-quickcheck',
    'ghc-tasty-rerun',
    'ghc-temporary',
    'ghc-terminal-size',
    'ghc-texmath',
    'ghc-text-manipulate',
    'ghc-text-metrics',
    'ghc-text-short',
    'ghc-text-zipper',
    'ghc-tf-random',
    'ghc-th-abstraction',
    'ghc-th-compat',
    'ghc-th-expand-syns',
    'ghc-th-lift',
    'ghc-th-lift-instances',
    'ghc-th-orphans',
    'ghc-th-reify-many',
    'ghc-these',
    'ghc-threads',
    'ghc-tidal',
    'ghc-time-compat',
    'ghc-time-locale-compat',
    'ghc-time-manager',
    'ghc-tls',
    'ghc-tls-session-manager',
    'ghc-torrent',
    'ghc-transformers-base',
    'ghc-transformers-compat',
    'ghc-turtle',
    'ghc-typed-process',
    'ghc-uglymemo',
    'ghc-unbounded-delays',
    'ghc-unicode-transforms',
    'ghc-union-find',
    'ghc-uniplate',
    'ghc-unix-compat',
    'ghc-unix-time',
    'ghc-unliftio',
    'ghc-unliftio-core',
    'ghc-unordered-containers',
    'ghc-uri',
    'ghc-uri-bytestring',
    'ghc-uri-bytestring-aeson',
    'ghc-uri-encode',
    'ghc-url',
    'ghc-utf8-light',
    'ghc-utf8-string',
    'ghc-uuid',
    'ghc-uuid-types',
    'ghc-vault',
    'ghc-vector',
    'ghc-vector-algorithms',
    'ghc-vector-binary-instances',
    'ghc-vector-builder',
    'ghc-vector-space',
    'ghc-vector-th-unbox',
    'ghc-void',
    'ghc-vty',
    'ghc-wai',
    'ghc-wai-app-static',
    'ghc-wai-cors',
    'ghc-wai-extra',
    'ghc-wai-handler-launch',
    'ghc-wai-logger',
    'ghc-wai-websockets',
    'ghc-warp',
    'ghc-warp-tls',
    'ghc-websockets',
    'ghc-with-location',
    'ghc-wizards',
    'ghc-wl-pprint',
    'ghc-wl-pprint-text',
    'ghc-word-wrap',
    'ghc-word8',
    'ghc-wreq',
    'ghc-x509',
    'ghc-x509-store',
    'ghc-x509-system',
    'ghc-x509-validation',
    'ghc-xdg-basedir',
    'ghc-xdg-userdirs',
    'ghc-xml',
    'ghc-xml-conduit',
    'ghc-xml-hamlet',
    'ghc-xml-types',
    'ghc-xmonad-contrib',
    'ghc-xss-sanitize',
    'ghc-yaml',
    'ghc-yesod',
    'ghc-yesod-core',
    'ghc-yesod-form',
    'ghc-yesod-persistent',
    'ghc-yesod-static',
    'ghc-zip-archive',
    'ghc-zlib',
    'ghc-zlib-bindings',
    'ghcid',
    'git-annex',
    'git-repair',
    'gitit',
    'gtk2hs-buildtools',
    'hadolint',
    'happy',
    'hledger',
    'hledger-ui',
    'hledger-web',
    'hlint',
    'hscolour',
    'hwk',
    'idris',
    'koji-tool',
    'lsfrom',
    'ormolu',
    'pagure-cli',
    'pandoc',
    'patat',
    'pkgtreediff',
    'rhbzquery',
    'rpmbuild-order',
    'shake',
    'tart',
    'unlambda',
    'xmobar',
    'xmonad',
]


# keep this sorted new -> old
MASSREBUILDS = {
    #f39 ftbfs bug tracker: TBA
    "f38":{
            "buildtag": 'f38-rebuild',  # tag to build from
            "epoch": '2023-01-18 10:30:00.000000',  # rebuild anything not built after this date
            "module_mass_rebuild_epoch": '2023-02-07T10:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_branching_epoch": '2023-02-07T10:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_rebuild_platform": "f38",
            # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
            "module_mass_branching_platform": "f38",
            # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
            "targets": ['f38-candidate', 'rawhide', 'f38'],
            # build targets to check for existing builds to skip rebuild
            "target": 'f38-rebuild',  # target to build into
            "desttag": 'f38',  # Tag where fixed builds go
            "product": "Fedora",  # for BZ product field
            "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
            "rawhide_version": "38",  # for next version calculation and other comments
            "tracking_bug": "2117176",  # Tracking bug for mass build failures
            "wikipage": "https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild",
            "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild

    },
    "f37":{
            "buildtag": 'f37-rebuild',  # tag to build from
            "epoch": '2022-07-20 17:30:00.000000',  # rebuild anything not built after this date
            "module_mass_rebuild_epoch": '2022-07-20T22:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_branching_epoch": '2022-02-08T22:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_rebuild_platform": "f37",
            # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
            "module_mass_branching_platform": "f37",
            # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
            "targets": ['f37-candidate', 'rawhide', 'f37'],
            # build targets to check for existing builds to skip rebuild
            "target": 'f37-rebuild',  # target to build into
            "desttag": 'f37',  # Tag where fixed builds go
            "product": "Fedora",  # for BZ product field
            "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
            "rawhide_version": "37",  # for next version calculation and other comments
            "tracking_bug": "2045102",  # Tracking bug for mass build failures
            "wikipage": "https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild",
            "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f36":
        {
            "buildtag": 'f36-rebuild',  # tag to build from
            "epoch": '2022-01-19 17:30:00.000000',  # rebuild anything not built after this date
            "module_mass_rebuild_epoch": '2022-01-19T22:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_branching_epoch": '2022-02-08T22:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_rebuild_platform": "f36",
            # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
            "module_mass_branching_platform": "f37",
            # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
            "targets": ['f36-candidate', 'rawhide', 'f36'],
            # build targets to check for existing builds to skip rebuild
            "target": 'f36-rebuild',  # target to build into
            "desttag": 'f36',  # Tag where fixed builds go
            "product": "Fedora",  # for BZ product field
            "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
            "rawhide_version": "36",  # for next version calculation and other comments
            "tracking_bug": "1992484",  # Tracking bug for mass build failures
            "wikipage": "https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild",
            "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
        },
    "f35":
        {
            "buildtag": 'f35-rebuild',  # tag to build from
            "epoch": '2021-07-21 15:30:00.000000',  # rebuild anything not built after this date
            "module_mass_rebuild_epoch": '2021-07-21T15:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_branching_epoch": '2022-08-10T22:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_rebuild_platform": "f35",
            # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
            "module_mass_branching_platform": "f36",
            # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
            "targets": ['f35-candidate', 'rawhide', 'f35'],
            # build targets to check for existing builds to skip rebuild
            "target": 'f35-rebuild',  # target to build into
            "desttag": 'f35',  # Tag where fixed builds go
            "product": "Fedora",  # for BZ product field
            "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
            "rawhide_version": "35",  # for next version calculation and other comments
            "tracking_bug": "1927309",  # Tracking bug for mass build failures
            "wikipage": "https://fedoraproject.org/wiki/Fedora_35_Mass_Rebuild",
            "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
        },
    "f34":
        {
            "buildtag": 'f34-rebuild',  # tag to build from
            "epoch": '2021-01-25 21:00:00.000000',  # rebuild anything not built after this date
            "module_mass_rebuild_epoch": '2021-01-25T21:00:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_branching_epoch": '2020-02-09T22:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_rebuild_platform": "f34",
            # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
            "module_mass_branching_platform": "f35",
            # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
            "targets": ['f34-candidate', 'rawhide', 'f34'],
            # build targets to check for existing builds to skip rebuild
            "target": 'f34-rebuild',  # target to build into
            "desttag": 'f34',  # Tag where fixed builds go
            "product": "Fedora",  # for BZ product field
            "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
            "rawhide_version": "34",  # for next version calculation and other comments
            "tracking_bug": "1868278",  # Tracking bug for mass build failures
            "wikipage": "https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild",
            "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
        },
    "f33":
        {
            "buildtag": 'f33-rebuild',  # tag to build from
            "epoch": '2020-07-27 10:00:00.000000',  # rebuild anything not built after this date
            "module_mass_rebuild_epoch": '2020-07-27T10:00:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_branching_epoch": '2020-08-11T12:30:00Z',
            # rebuild anything not built after this date for modules
            "module_mass_rebuild_platform": "f33",
            # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
            "module_mass_branching_platform": "f34",
            # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
            "targets": ['f33-candidate', 'rawhide', 'f33'],
            # build targets to check for existing builds to skip rebuild
            "target": 'f33-rebuild',  # target to build into
            "desttag": 'f33',  # Tag where fixed builds go
            "product": "Fedora",  # for BZ product field
            "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
            "rawhide_version": "33",  # for next version calculation and other comments
            "tracking_bug": "1803234",  # Tracking bug for mass build failures
            "wikipage": "https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild",
            "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
        },
    "f32":
    {
        "buildtag": 'f32-rebuild',  # tag to build from
        "epoch": '2020-01-28 03:30:00.000000',  # rebuild anything not built after this date
        "module_mass_rebuild_epoch": '2020-01-28T03:30:00Z',  # rebuild anything not built after this date for modules
        "module_mass_branching_epoch": '2020-02-11T23:30:00Z',  # rebuild anything not built after this date for modules
        "module_mass_rebuild_platform": "f32",  # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
        "module_mass_branching_platform": "f33",  # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
        "targets": ['f32-candidate', 'rawhide', 'f32'],  # build targets to check for existing builds to skip rebuild
        "target": 'f32-rebuild',  # target to build into
        "desttag": 'f32',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
        "rawhide_version": "32",  # for next version calculation and other comments
        "tracking_bug": "1750908",  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f31":
    {
        "buildtag": 'f31-rebuild',  # tag to build from
        "epoch": '2019-07-24 09:40:00.000000',  # rebuild anything not built after this date
        "module_mass_rebuild_epoch": '2019-07-24T09:40:00Z',  # rebuild anything not built after this date for modules
        "module_mass_branching_epoch": '2019-08-13T17:00:00Z',  # rebuild anything not built after this date for modules
        "module_mass_rebuild_platform": "f31",  # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
        "module_mass_branching_platform": "f32",  # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
        "targets": ['f31-candidate', 'rawhide', 'f31'],  # build targets to check for existing builds to skip rebuild
        "target": 'f31-rebuild',  # target to build into
        "desttag": 'f31',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
        "rawhide_version": "31",  # for next version calculation and other comments
        "tracking_bug": "1700317",  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f30":
    {
        "buildtag": 'f30-rebuild',  # tag to build from
        "epoch": '2019-01-31 10:10:00.000000',  # rebuild anything not built after this date
        "module_mass_rebuild_epoch": '2019-02-13T18:30:00Z',  # rebuild anything not built after this date for modules
        "module_mass_branching_epoch": '2019-03-04T18:00:00Z',  # rebuild anything not built after this date for modules
        "module_mass_rebuild_platform": "f30",  # rebuild all modules that has build time dependency on this platform, this is used during mass rebuild time
        "module_mass_branching_platform": "f31",  # rebuild all modules that has run time dependency on this platform, this is used during mass branching time
        "targets": ['f30-candidate', 'rawhide', 'f30'],  # build targets to check for existing builds to skip rebuild
        "target": 'f30-rebuild',  # target to build into
        "desttag": 'f30',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "rawhide",  # for BZ version field, rawhide before branching or xx after branching
        "rawhide_version": "30",  # for next version calculation and other comments
        "tracking_bug": "1674516",  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f29":
    {
        "buildtag": 'f29-rebuild',  # tag to build from
        "epoch": '2018-07-12 17:00:00.000000',  # rebuild anything not built after this date
        "targets": ['f29-candidate', 'rawhide', 'f29'],  # build targets to check for existing builds to skip rebuild
        "target": 'f29-rebuild',  # target to build into
        "desttag": 'f29',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "29",  # for BZ version field
        "tracking_bug": 1602938,  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
        "current_rawhide": "29",
    },
    "f28":
    {
        "buildtag": 'f28-rebuild',  # tag to build from
        "epoch": '2018-02-06 01:20:06.000000',  # rebuild anything not built after this date
        "targets": ['f28-candidate', 'rawhide', 'f28'],  # build targets to check for existing builds to skip rebuild
        "target": 'f28-rebuild',  # target to build into
        "desttag": 'f28',  # Tag where fixed builds go
        "product": "Fedora",  # for BZ product field
        "version": "28",  # for BZ version field
        "tracking_bug": 1555378,  # Tracking bug for mass build failures
        "wikipage": "https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild",
        "pkg_skip_list": PKG_SKIP_LIST,  # packages to skip in rebuild
    },
    "f27":
    {
        "epoch": '2017-07-31 11:20:00.000000',
    }
}
