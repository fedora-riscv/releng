#!/usr/bin/python

# secondary-sync - a command line tool to sync all fedora secondary arches
# from the hubs to a central mirror
#
# Copyright (C) 2011-2013 Red Hat, Inc.
# SPDX-License-Identifier:      GPL-2.0+
# Author(s):  Dennis Gilmore <dennis@ausil.us>

import rpm
import os
import logging
import subprocess
import argparse
import createrepo
import sys
import re


CANONARCHES = ['arm', 'ppc', 's390']
ARCHES = {'arm': ['arm', 'armhfp', 'aarch64'],
          'ppc': ['ppc', 'ppc64', 'ppc64le'],
          's390': ['s390', 's390x']}
#TARGETPATH = '/srv/pub/fedora-secondary/test/'
TARGETPATH = '/srv/pub/fedora-secondary/'



# Setup our logger
# Null logger to avoid spurrious messages, add a handler in app code
class NullHandler(logging.Handler):
    def emit(self, record):
        pass

h = NullHandler()

# This is our log object,
log = logging.getLogger("secondary-sync")
# Add the null handler
log.addHandler(h)


def notify(msg):
    import fedmsg
    kwargs = dict(
        modname='releng',
        topic='secondary.updates.rsync.complete',
        msg=msg,

        # These direct us to talk to a fedmsg-relay living somewhere.
        active=True,
        name="relay_inbound",
        )
    fedmsg.publish(**kwargs)


def _run_command(cmd, shell=False, env=None, pipe=[], cwd=None):
    """Run the given command.
    Will determine if caller is on a real tty and if so stream to the tty
    Or else will run and log output.
    cmd is a list of the command and arguments
    shell is whether to run in a shell or not, defaults to False
    env is a dict of environment variables to use (if any)
    pipe is a command to pipe the output of cmd into
    cwd is the optional directory to run the command from
    Raises on error, or returns nothing.

    """

    # This should contain the rsync output after it ran.
    output = ""

    # Process any environment variables.
    environ = os.environ
    if env:
        for item in env.keys():
            log.debug('Adding %s:%s to the environment' %
                           (item, env[item]))
            environ[item] = env[item]
    # Check if we're supposed to be on a shell.  If so, the command must
    # be a string, and not a list.
    command = cmd
    pipecmd = pipe
    if shell:
        command = ' '.join(cmd)
        pipecmd = ' '.join(pipe)
    # Check to see if we're on a real tty, if so, stream it baby!
    if sys.stdout.isatty():
        if pipe:
            log.debug('Running %s | %s directly on the tty' %
                           (' '.join(cmd), ' '.join(pipe)))
        else:
            log.debug('Running %s directly on the tty' %
                            ' '.join(cmd))
        try:
            if pipe:
                # We're piping the stderr over too, which is probably a
                # bad thing, but rpmbuild likes to put useful data on
                # stderr, so....
                proc = subprocess.Popen(command, env=environ,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, shell=shell,
                                        cwd=cwd)
                subprocess.check_call(pipecmd, env=environ,
                                      stdout=sys.stdout,
                                      stderr=sys.stderr,
                                      stdin=proc.stdout,
                                      shell=shell,
                                      cwd=cwd)
                (output, err) = proc.communicate()
                if proc.returncode:
                   print 'Non zero exit'
            else:
                proc = subprocess.Popen(command, env=environ,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, shell=shell,
                                        cwd=cwd)
                # We want to output on stdout and capture the output for parsing
                for line in iter(proc.stdout.readline, ''):
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    output += line
        except (subprocess.CalledProcessError,
                OSError), e:
            print e
        except KeyboardInterrupt:
            print "interputed by user"
    else:
        # Ok, we're not on a live tty, so pipe and log.
        if pipe:
            log.debug('Running %s | %s and logging output' %
                          (' '.join(cmd), ' '.join(pipe)))
        else:
            log.debug('Running %s and logging output' %
                           ' '.join(cmd))
        try:
            if pipe:
                proc1 = subprocess.Popen(command, env=environ,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT,
                                         shell=shell,
                                         cwd=cwd)
                proc = subprocess.Popen(pipecmd, env=environ,
                                         stdin=proc1.stdout,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE, shell=shell,
                                         cwd=cwd)
                output, error = proc.communicate()
            else:
                proc = subprocess.Popen(command, env=environ,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, shell=shell,
                                        cwd=cwd)
                output, error = proc.communicate()
        except OSError, e:
            raise rpkgError(e)
        log.info(output)
        if proc.returncode:
            print ('Command %s returned code %s with error: %s' %
                              (' '.join(cmd),
                               proc.returncode,
                               error))
    result = re.search('.*Literal data: (.*) bytes.*', output, re.MULTILINE)
    try:
        transferred = result.group(1)
    except:
        transferred = "0"
    result = re.findall('.*deleting.*', output, re.MULTILINE)
    if result:
        deleted = str(len(result))
    else:
        deleted = "0"

    return (transferred, deleted)

def syncArch(arch, repodata, fedmsg=False):
    '''
    Sync a binary rpm tree pass in arch and True/False for syncing repodata or not
    syncing repodata does a --delete-after
    '''
    cmd = ['rsync', '-avhHp', '--exclude=.snapshot', '--exclude=archive', '--exclude=SRPMS', '--exclude=source']
    for canonarch in CANONARCHES:
        if not canonarch == arch:
            archlist = ARCHES[canonarch]
            for subarch in archlist:
                cmd.extend(['--exclude=%s' % subarch])
    if repodata:
        cmd.extend(['--delete-after'])
    else:
        cmd.extend(['--exclude=repodata'])
    cmd.extend(['rsync://%s.koji.fedoraproject.org/fedora-%s' % (arch, arch)])
    cmd.extend([TARGETPATH])
    log.debug(cmd)
    if not opts.only_show:
        transferred, deleted = _run_command(cmd)
        if fedmsg and (transferred != "0" or deleted != "0"):
            results = dict(deleted=deleted, bytes=transferred, arch=arch)
            notify(results)
    else:
        print cmd

def syncSRPM(srpm, arch, dest, source, fedmsg=False):
    if not os.path.isdir(dest):
        os.makedirs(dest)
    cmd = ['rsync', '-avhH', 'rsync://%s.koji.fedoraproject.org/fedora-%s/%s/%s' % (arch, arch, source, srpm), '%s/%s' % (dest, srpm)]
    log.debug(cmd)
    if not opts.only_show:
        transferred, deleted = _run_command(cmd)
        if fedmsg and (transferred != "0" or deleted != "0"):
            results = dict(deleted=deleted, bytes=transferred, arch=arch)
            notify(results)
    else:
        print cmd

def getSRPM(rpmfilename):
    """ get the SRPM of a given RPM. """
    ts = rpm.TransactionSet()
    ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES) 
    fd = os.open(rpmfilename, os.O_RDONLY)
    h = None
    try:
        h = ts.hdrFromFdno(fd)
    except rpm.error, e:
        if str(e) == "error reading package header ":
           print "rpmfile: %s" % rpmfilename
           print str(e)
           return None
    os.close(fd)
    if h == None:
         print "Issues with rpm: %s" % rpmfilename
         return None
    return h.sprintf('%{SOURCERPM}')

def srpmLocation(base, package):
    ''' 
    Takes a base path for the sources rpm
    Returns the target path the arch of the hub and path on the hub to find the source
    '''
    basearch = None
    for arch in CANONARCHES:
        if not base.find(arch) == -1:
            hubarch = arch
            for f in base.split('/'):
                if f.startswith(arch):
                    basearch = f
                    break
            break

    if not (base.endswith(basearch) or base.endswith("%s/%s" % (basearch, package[1]))) :
        target = base.replace('%s/os/Packages' % basearch, 'source/SRPMS')
    else:
        target = base.replace(basearch, 'SRPMS')
    source = target.replace(TARGETPATH, '', 1)
    return (hubarch, target, source)

def main(opts):
    # Sync the given arch or all arches unless told to not sync
    if not opts.no_sync:
         if opts.onlyarch:
             syncArch(opts.onlyarch, False)
             syncArch(opts.onlyarch, True, opts.fedmsg)
         else:
             for arch in CANONARCHES:
                 syncArch(arch, False)
                 syncArch(arch, True, opts.fedmsg)

    # work out what SRPMS we need and what can be removed.
    srpms = {}
    existing_srpms = {}
    to_sync_srpms = {}
    to_delete_srpms = {}
    sourcerepo = []
    for root, dirs, files in os.walk(TARGETPATH):
        if not root.find('/archive/') == -1 or not root.find('/.snapshot/') == -1 :
            continue
        if root == []:
            continue
        if root.find('debug'):
            continue
        if root.find('drpms'):
            continue
        if root.find('SRPMS'):
            sourcerepo.append(root)
        for name in files:
            if name.endswith('rpm') and not name.endswith('src.rpm'):
                srpmfile = getSRPM(os.path.join( root, name))
                if not srpmfile == None:
                    print "getting data for %s" % name
                    srpms[srpmfile] = srpmLocation(root, name)
            if name.endswith('src.rpm'):
                existing_srpms[name] = root

    for srpm in zip(srpms.keys(), srpms.values()):
        if srpm[0] not in existing_srpms.keys() and srpm[0] not in to_sync_srpms.keys():
            print "Need: %s  At: %s" % (srpm[0], srpm[1])
            to_sync_srpms[srpm[0]] = srpm[1] 

    for srpm in zip(existing_srpms.keys(), existing_srpms.values()):
        if srpm[0] not in srpms.keys() and srpm[0] not in to_delete_srpms.keys():
            print "To Delete: %s" % srpm[0]
            to_delete_srpms[srpm[0]] = srpm[1]


    for files in zip(to_sync_srpms.keys(), to_sync_srpms.values()):
        print files
        srpm = files[0]
        arch = files[1][0]
        dest = files[1][1]
        source = files[1][2]
        if not opts.only_show:
            syncSRPM(srpm, arch, dest, source, opts.fedmsg)

    for files in zip(to_delete_srpms.keys(), to_delete_srpms.values()):
        srpmfile = os.path.join(files[1], files[0])
        print "Removing: %s" % srpmfile
        if not opts.only_show:
            os.unlink(srpmfile)

    for repo in sourcerepo:
        print "updating repo metadata in %s" % repo
        if not opts.only_show:
            cmd = ['createrepo', '-d', '--update', '--unique-md-filenames', repo]
            print cmd
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        cwd=repo, stderr=subprocess.PIPE)
                output, error = proc.communicate()
            except OSError, e:
                print e
            if error:
                if sys.stdout.isatty():
                    sys.stderr.write(error)
                #else:
                    # Yes, we could wind up sending error output to stdout in the
                    # case of no local tty, but I don't have a better way to do this.
                    #self.log.info(error)
            if proc.returncode:
                print "error making repodata %s", proc.returncode
        

if __name__ == '__main__':
    opt_p = argparse.ArgumentParser(usage = "%(prog)s [OPTIONS] ")
    opt_p.add_argument('-a', '--arch', action='store', dest='onlyarch',
                     default=False, help="sync only the given arch.")
    opt_p.add_argument('-s', '--show', action='store_true', dest='only_show',
                     default=False, help="Show what would be done but dont actually do it.")
    opt_p.add_argument('-n', '--no-sync', action='store_true', dest='no_sync',
                     default=False, help="Skip syncing new bits.")
    opt_p.add_argument('--disable-fedmsg', dest="fedmsg", action="store_false",
                     help="Disable fedmsg notifications", default=True)

    args, extras = opt_p.parse_known_args()

    main(args)

