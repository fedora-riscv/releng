#!/usr/bin/env python3
# SPDX-License-Identifier: MIT

import argparse
from datetime import datetime, timezone
import logging
import queue
import threading

import bugzilla
import koji

from massrebuildsinfo import MASSREBUILDS

LOGGER = logging.getLogger(__name__)

def koji2datetime(d):
    return datetime.fromisoformat(d)

def bug2str(bug):
    return f"{bug.id} ({bug.summary})"

def release2disttag(release):
    assert release.startswith('f')
    return 'fc' + release[1:]

def parse_bool(s):
    if s.lower() in {'0', 'false', 'no'}:
        return False
    if s.lower() in {'1', 'true', 'yes'}:
        return True
    raise ValueError

def bug_closer(to_close, bz, dry_run):
    while True:
        item = to_close.get()
        if not item:
            break

        bug, build = item
        update = bz.build_update(status="CLOSED",
                                 resolution="NEXTRELEASE",
                                 comment=f"""\
There has been at least one successfull build after mass rebuild.

{build["nvr"]}: https://koji.fedoraproject.org/koji/buildinfo?buildID={build["id"]}
""")
        LOGGER.info(f"{bug2str(bug)}\n"
                     "  → Closing")
        if not dry_run:
            bz.update_bugs([bug.id], update)

        to_close.task_done()

def main():
    rebuilds_info = {k: v for k, v in MASSREBUILDS.items() if "buildtag" in v}

    parser = argparse.ArgumentParser(description="Close FTBFS bugs which have been fixed")
    verbose_opt = parser.add_mutually_exclusive_group()
    verbose_opt.add_argument("-d", "--debug", action="store_true")
    verbose_opt.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("-t", "--threads", type=int, default=0)
    parser.add_argument("--strict-disttag", type=parse_bool,
                        help='Only close bugs where the build tag matches the release '
                             '(ignore builds for different releases)',
                        nargs='?', const=True, metavar='BOOL')
    parser.add_argument("--strict-title", type=parse_bool,
                        help='Only close bugs where the title matches the expected pattern '
                             '(<component>: FTBFS in ...)',
                        nargs='?', const=True, metavar='BOOL',
                        default=True)
    parser.add_argument("release", choices=rebuilds_info.keys())
    args = parser.parse_args()

    # Setup logging
    handler = logging.StreamHandler()
    LOGGER.addHandler(handler)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    if args.verbose:
        LOGGER.setLevel(level=logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(level=logging.INFO)
        handler.setLevel(logging.INFO)

    if args.threads <= 0:
        import multiprocessing
        args.threads = multiprocessing.cpu_count()

    massrebuild = rebuilds_info[args.release]
    rebuild_time = koji2datetime(massrebuild["epoch"]).replace(tzinfo=timezone.utc)

    bz = bugzilla.Bugzilla("https://bugzilla.redhat.com")
    ks = koji.ClientSession("https://koji.fedoraproject.org/kojihub")

    query = bz.build_query(product=massrebuild["product"],
                           version=massrebuild["version"],
                           blocked=str(massrebuild["tracking_bug"]),
                           include_fields=["id",
                                           "is_open",
                                           "summary",
                                           "component",
                                           "creation_time"])
    ftbfs = bz.query(query)
    tag = ks.getTagID(massrebuild["buildtag"], strict=True)

    bugs = []
    ks.multicall = True
    for bug in ftbfs:
        if not bug.is_open:
            # DO NOT TOUCH CLOSED BUGZ!
            LOGGER.debug(f"{bug2str(bug)}\n"
                          "  → Skipping closed bug")
            continue
        if (args.strict_title and
            not bug.summary.startswith(f"{bug.component}: FTBFS in F")):
            # They might need special care
            LOGGER.debug(f"{bug2str(bug)}\n"
                          "  → Skipping bug with non-standard name")
            continue

        bugs.append(bug)
        ks.getLatestBuilds(tag, package=bug.component)
    builds = [ret[0] for ret in ks.multiCall(strict=True)]

    # Spawn workers
    to_close = queue.Queue()
    threads = []
    for _ in range(args.threads):
        t = threading.Thread(target=bug_closer, args=(to_close, bz, args.dry_run))
        t.start()
        threads.append(t)

    for bug, builds in zip(bugs, builds):
        builds = [build for build in builds if koji2datetime(build["creation_time"]) >= rebuild_time]
        if not builds:
            LOGGER.debug(f"{bug2str(bug)}\n"
                          "  → No successful builds")
            continue
        for build in builds:
            if args.strict_disttag:
                nvr = build['nvr']
                if not nvr.endswith('.' + release2disttag(args.release)):
                    LOGGER.debug(f"{bug2str(bug)}\n"
                                 "  → Ignoring build with wrong nvr ({nvr})")
                    continue
            to_close.put((bug, build))

    # Wait untill all bugs closed
    to_close.join()

    # Stop workers
    for _ in range(args.threads):
        to_close.put(None)
    for t in threads:
        t.join()

if __name__ == "__main__":
    main()
