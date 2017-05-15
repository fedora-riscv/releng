#!/usr/bin/python
#
# mass-rebuild.py - A utility to rebuild packages.
#
# Copyright (C) 2009-2013 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
#
# Authors:
#     Jesse Keating <jkeating@redhat.com>
#

import koji
import os
import subprocess
import sys
import operator

# Set some variables
# Some of these could arguably be passed in as args.
buildtag = 'f27' # tag to build from
secondbuildtag = 'f26' # tag to build from
epoch = '2017-05-12 00:00:00.000000' # rebuild anything not built after this date
user = 'Fedora Release Engineering <rel-eng@lists.fedoraproject.org>'
comment = '- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_27_Mass_Rebuild'
workdir = os.path.expanduser('~/massbuild-gcc')
enviro = os.environ
targets = ['f26-gcc-abi-rebuild','f27-gcc-abi-rebuild']
branches = ['master', 'f26']
enviro['CVS_RSH'] = 'ssh' # use ssh for cvs

pkg_skip_list = ['fedora-release', 'fedora-repos', 'generic-release', 'redhat-rpm-config', 'shim', 'shim-signed', 'kernel', 'grub2', 'gcc', 'glibc']

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
    except subprocess.CalledProcessError, e:
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
                               stdout=subprocess.PIPE)
    except BaseException, e:
        sys.stderr.write('%s failed %s: %s\n' % (pkg, action, e))
        return 0
    result = pid.communicate()[0].rstrip('\n')
    return result


# Create a koji session
kojisession = koji.ClientSession('https://koji.fedoraproject.org/kojihub')

# Generate a list of packages to iterate over
pkgs = ['libtorrent','ceres-solver','codeblocks','opencv','mmseq','zhu3d','libmediainfo','fawkes','fmt','step','mlpack','hyperrogue','root','vxl','repsnapper','tellico','pcl','avogadro2-libs','znc','purple-line','nload','jsoncpp','libepubgen','device-mapper-persistent-data','libgnomecanvasmm26','kig','coan','plotmm','fuse-emulator-utils','eris','harmonyseq','afflib','libopenraw','coin-or-Alps','ccgo','cfdg','linbox','recoll','votca-csg','flxmlrpc','coin-or-CoinUtils','stage','glogg','mongo-cxx-driver','libmediainfo','gsmartcontrol','ochusha','verilator','rb_libtorrent','rmol','exempi','pdns-recursor','gparted','ardour2','librime','mm3d','qt5-qtconnectivity','airtsp','normaliz','vulkan','kf5-kio','gpsim','monotone','mmapper','ember','qpdf','wireshark','mapserver','filezilla','extremetuxracer','mypaint','alliance','kstars','qgis','ardour5','opencv','qcad','passenger','calf','qt5-qtbase','kopete','digikam','nodejs-mapnik','stellarium','opencity','icecat','qm-vamp-plugins','pingus','abiword','goldendict','gtengine','condor','cloudy','healpix','latte-integrale','celestia','din','perl-Boost-Geometry-Utils','libpar2','libvisio','coin-or-Bcp','love','3Depict','flrig','libpagemaker','pan','engauge-digitizer','libzmf','scorchwentbonkers','libfilezilla','v4l-utils','gdl','uhd','libfreehand','llvm3.9','sword','nextcloud-client','protobuf','crawl','libmspub','pynac','istatd','kblocks','libetonyek','kf5-knotifications','fawkes','minion','tcpflow','ignition-math','libwps','fcl','ergo','libpwiz','endless-sky','webkitgtk4','apitrace','libghemical','coin-or-OS','binutils','coin-or-Dip','adanaxisgpl','extundelete','synfig','stxxl','libminc','cairomm','amftools','mingw-qt5-qtbase','gnuplot','tellico','rdfind','freefem++','rocs','kcachegrind','rosegarden4','libmp4v2','qesteidutil','qcustomplot','code-editor','rcsslogplayer','pulseview','libdxfrw','mlpack','worker','aseman-qt-tools','stockfish','massif-visualizer','cryptominisat','powertop','usbguard','thrift','mmseq','fparser','audacity','poedit','panoglview','sonic-visualiser','mathex','getdp','librealsense','onboard','libgltf','aria2','innoextract','fritzing','flamerobin','gambas3','openmsx','oxygen-gtk2','asymptote','repsnapper','openscad','givaro','ompl','bionetgen','xrootd','qt5-qt3d','coot','glob2','nyquist','avogadro2-libs','cmake','libcec','qwtplot3d','kdevplatform','xapian-core','zpaq','libstaroffice','link-grammar','synergy','dasher','vcftools','ldc','lnav','coin-or-Couenne','dwlocstat','gimagereader','zimlib','assimp','coin-or-lemon','wxGTK3','sdformat','liblsl','faust','hugin','coin-or-Cgl','rtorrent','dssp','zhu3d','botan','podofo','xfce4-hardware-monitor-plugin','libffado','grive2','coin-or-Ipopt','jmtpfs','flare-engine','lhapdf','airinv','liborigin2','vdrift','xylib','libcdr','plasma-workspace','adevs','plee-the-bear','libkdtree++','votca-xtp','ginac','libdigidocpp','qt','mapnik','hyperrogue','antimony','qlandkartegt','zorba','gdb','orocos-kdl','libmwaw','cube','libfplll','rawtherapee','skyviewer','xsd','stdair','tarantool','wt','zeromq','votca-tools','par2cmdline','leveldb','vfrnav','ispc','kst','heaptrack','brial','wcm','muse','kf5-akonadi-server','yadex','lifeograph','scantailor','erlang-eleveldb','fmt','osmium-tool','libcmis','exiv2','ghemical','gwenview','scram','step','qt5-qtlocation','icedtea-web','stk','vxl','gimp-dbp','shiboken','fldigi','coin-or-Cbc','gxemul','mathicgb','orsa','dnsdist','wfmath','brewtarget','compat-wxGTK3-gtk2','gtatool','flann','simple-mtpfs','codeblocks','povray','qtwebkit','texstudio','sleuthkit','openoffice.org-diafilter','libndn-cxx','patchelf','qt5-qtwebkit','cvc4','gjs','figtoipe','dvgrab','adobe-source-libraries','galera','sockperf','pgRouting','ceph','community-mysql','mecab','kf5-kactivities-stats','libwpd','erlang-basho_metrics','libodb','libjson-rpc-cpp','vdr-vnsiserver','guitarix','gmsh','gqrx','cryptominisat4','openCOLLADA','coin-or-FlopC++','ncrack','crrcsim','kdevelop','enigma','yosys','mpqc','libjingle','ocrad','mysql++','swig','dosbox','fityk','gnucap','xplanet','frepple','zeitgeist','beediff','extrema','coin-or-Bonmin','lldb','wxmacmolplt','kalarm','lilypond','stardict','gobby05','tapkee','qdigidoc','slic3r-prusa3d','coin-or-Bcps','slic3r','openigtlink','engrid','psi4','musique','lziprecover','qblade','voro++','pdfedit','libwpg','coin-or-Clp','pavucontrol','lld','indi-eqmod','openlierox','lshw','barry','gazebo','tomahawk','kismet','polyclipping','libQGLViewer','opencc','ceres-solver','vips','procinfo-ng','liborigin','eclib','chromaprint','libzypp','coin-or-Blis','owncloud-client','pcb2gcode','muParser','cxsc','task','xtide','fmit','mariadb','libint2','supertux','libabigail','krita','btbuilder','python-mapnik','freeorion','kicad','asgp','root','mingw-qt','supertuxkart','gammaray','warsow','warzone2100','sagemath','cross-gcc','lincity-ng','widelands','vtk','texlive','insight','marble-widget','zaz','marble-subsurface','percona-xtrabackup','polymake','blender','mscore','efl','marsshooter','seqan','mozjs45','thunderbird']

print 'Checking %s packages...' % len(pkgs)

# Loop over each package
for pkg in pkgs:
    name = pkg

    # some package we just dont want to ever rebuild
    if name in pkg_skip_list:
        print 'Skipping %s, package is explicitely skipped' % name
        continue

    # Check out git
    fedpkgcmd = ['fedpkg', 'clone', name]
    print 'Checking out %s' % name
    if runme(fedpkgcmd, 'fedpkg', name, enviro):
        continue

    # Check for a checkout
    if not os.path.exists(os.path.join(workdir, name)):
        sys.stderr.write('%s failed checkout.\n' % name)
        continue

    # Check for a noautobuild file
    #f os.path.exists(os.path.join(workdir, name, 'noautobuild')):
        # Maintainer does not want us to auto build.
    #   print 'Skipping %s due to opt-out' % name
    #   continue

    # check the git hashes of the branches
    gitcmd = ['git', 'rev-parse', 'origin/master']
    print 'getting git hash for master'
    masterhash = runmeoutput(gitcmd, 'git', name, enviro, cwd=os.path.join(workdir, name))
    if masterhash == 0:
        sys.stderr.write('%s has no git hash.\n' % name)
        break
 
    gitcmd = ['git', 'rev-parse', 'origin/%s' % secondbuildtag ]
    print 'getting git hash for %s' % secondbuildtag
    secondhash = runmeoutput(gitcmd, 'git', name, enviro, cwd=os.path.join(workdir, name))
    if secondhash == 0:
        sys.stderr.write('%s has no git hash.\n' % name)
        break

    for branch in [buildtag, secondbuildtag]:
        if branch == buildtag:
            target = targets[0]
        else:
            target = targets[1]

        if branch == secondbuildtag:
            # switch branch
            fedpkgcmd = ['fedpkg', 'switch-branch', secondbuildtag ]
            print 'switching %s to %s' % (name, secondbuildtag)
            if runme(fedpkgcmd, 'fedpkg', name, enviro, cwd=os.path.join(workdir, name)):
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

        if branch == buildtag or masterhash != secondhash:
            # rpmdev-bumpspec
            bumpspec = ['rpmdev-bumpspec', '-u', user, '-c', comment,
                        os.path.join(workdir, name, spec)]
            print 'Bumping %s' % spec
            if runme(bumpspec, 'bumpspec', name, enviro):
                continue

            # git commit
            commit = ['fedpkg', 'commit', '-p', '-m', comment]
            print 'Committing changes for %s' % name
            if runme(commit, 'commit', name, enviro,
                         cwd=os.path.join(workdir, name)):
                continue
        else:
            gitmergecmd = ['git', 'merge', 'master']
            print "merging master into %s" % secondbuildtag
            if runme(gitmergecmd, 'git', name, enviro,
                         cwd=os.path.join(workdir, name)):
                continue
            # git push
            push = ['git', 'push']
            print 'push changes for %s' % name
            if runme(push, 'push', name, enviro,
                     cwd=os.path.join(workdir, name)):
                continue

        # build
        build = ['fedpkg', 'build', '--nowait', '--background', '--target', target]
        print 'Building %s' % name
        runme(build, 'build', name, enviro, 
              cwd=os.path.join(workdir, name))
