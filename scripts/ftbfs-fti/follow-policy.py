#!/usr/bin/python3

import collections
import datetime
import os
import re
import sys

import bugzilla
import click
import jinja2
import solv

TEMPLATE_DIR = os.path.dirname(os.path.realpath(__file__))

NOW = datetime.datetime.now()
TRACKERS = {
    "F30FailsToInstall": 1700323,
    "F31FailsToInstall": 1700324,
    "F32FailsToInstall": 1750909,
    "F33FailsToInstall": 1803235,
    "F30FTBFS": 1674516,
    "F31FTBFS": 1700317,
    "F32FTBFS": 1750908,
    "F33FTBFS": 1803234,
}


def _bzdate_to_python(date):
    return datetime.datetime.strptime(str(date), "%Y%m%dT%H:%M:%S")


def handle_orphaning(bug):
    bz = bug.bugzilla
    creation_time = _bzdate_to_python(bug.creation_time)
    diff = NOW - creation_time
    if diff < datetime.timedelta(weeks=1):
        print(
            f"Skipping because week did not pass yet since creation time ({creation_time})",
            file=sys.stderr,
        )
        return

    # Only reliable way to get whether needinfos were set is go through history
    history = bug.get_history_raw()["bugs"][0]["history"]
    needinfos = [
        u
        for u in history
        for c in u["changes"]
        if f"needinfo?({bug.assigned_to})" in c["added"]
    ]
    bzupdate = None
    flag = {"name": "needinfo", "status": "?", "requestee": bug.assigned_to}
    if not needinfos:
        print("Asking for a first needinfo")
        bzupdate = bz.build_update(
            comment="""Hello,

This is the first reminder (step 3 from https://docs.fedoraproject.org/en-US/fesco/Fails_to_build_from_source_Fails_to_install/#_package_removal_for_long_standing_ftbfs_and_fti_bugs).""",
            flags=[flag],
        )
    else:
        try:
            needinfo_after_week = next(
                _bzdate_to_python(n["when"])
                for n in needinfos
                if NOW - _bzdate_to_python(n["when"]) >= datetime.timedelta(weeks=1)
            )
        except StopIteration:
            print(
                f"No needinfo older than 1 week (oldest is from {_bzdate_to_python(needinfos[0]['when'])})",
                file=sys.stderr,
            )
            return
        try:
            needinfo_after_four_weeks = next(
                _bzdate_to_python(n["when"])
                for n in needinfos
                if _bzdate_to_python(n["when"]) - needinfo_after_week
                >= datetime.timedelta(weeks=3)
            )
        except StopIteration:
            print(
                f"No needinfo older than 3 weeks starting from first needinfo ({needinfo_after_week})",
                file=sys.stderr,
            )
            if NOW - needinfo_after_week >= datetime.timedelta(weeks=3):
                print("Asking for another needinfo")
                # RHBZ can have multiple needinfo flags, but python-bugzilla does not like it much
                # https://github.com/python-bugzilla/python-bugzilla/issues/118
                flags = [f for f in bug.flags if f["name"] == "needinfo"]
                if flags:
                    # If there are any needinfos, we will drop all of them and then create a new one
                    bz.update_bugs(
                        [bug.id],
                        bz.build_update(
                            flags=[
                                {"name": "needinfo", "id": f["id"], "status": "X"}
                                for f in flags
                            ]
                        ),
                    )
                bzupdate = bz.build_update(
                    comment="""Hello,

This is the second reminder (step 4 from https://docs.fedoraproject.org/en-US/fesco/Fails_to_build_from_source_Fails_to_install/#_package_removal_for_long_standing_ftbfs_and_fti_bugs).""",
                    flags=[flag],
                )
                return
        if NOW - needinfo_after_four_weeks >= datetime.timedelta(weeks=4):
            print("Opening releng ticket")
            # TODO: Implement
        else:
            print(
                f"No needinfo older than 4 weeks starting from second needinfo ({needinfo_after_four_weeks})",
                file=sys.stderr,
            )

    if bzupdate is not None:
        bz.update_bugs([bug.id], bzupdate)


def find_broken_packages(pool):
    solver = pool.Solver()
    solver.set_flag(solv.Solver.SOLVER_FLAG_IGNORE_RECOMMENDED, True)
    # Check for packages installability
    candq = set(pool.solvables)
    while candq:
        jobs = [
            pool.Job(
                solv.Job.SOLVER_SOLVABLE
                | solv.Job.SOLVER_INSTALL
                | solv.Job.SOLVER_WEAK,
                p.id,
            )
            for p in candq
        ]
        solver.solve(jobs)
        candq_n = candq - set(pool.id2solvable(s) for s in solver.raw_decisions(1))
        if candq == candq_n:
            # No more packages is possible to resolve
            break
        candq = candq_n

    ftbfs = {}
    fti = collections.defaultdict(dict)

    if not candq:
        return ftbfs, fti

    for s in candq:
        problems = solver.solve(
            [pool.Job(solv.Job.SOLVER_SOLVABLE | solv.Job.SOLVER_INSTALL, s.id)]
        )
        if not problems:
            continue
        elif len(problems) > 1:
            raise AssertionError
        problem = problems[0]

        if s.arch in {"src", "nosrc"}:
            srcname = s.name
            tmp = ftbfs[s.name] = []
        else:
            srcname = s.lookup_sourcepkg().rsplit("-", 2)[0]
            tmp = fti[srcname][s.name] = []

        for rule in problem.findallproblemrules():
            if rule.type != solv.Solver.SOLVER_RULE_PKG:
                raise NotImplementedError(f"Unsupported rule type: {rule.type}")
            tmp.append(
                [
                    {
                        "type": info.type,
                        "dep": info.dep,
                        "solvable": info.solvable,
                        "othersolvable": info.othersolvable,
                        "str": info.problemstr(),
                    }
                    for info in rule.allinfos()
                ]
            )

    return ftbfs, fti


@click.command()
def follow_policy():
    pool = solv.Pool()
    pool.setarch()

    for r in ("koji",):  # "koji-source"):
        repo = pool.add_repo(r)
        f = solv.xfopen(f"/var/cache/dnf/{r}.solv")
        repo.add_solv(f)
        f.close()

    pool.addfileprovides()
    pool.createwhatprovides()

    ftbfs, fti = find_broken_packages(pool)

    bz = bugzilla.Bugzilla("https://bugzilla.redhat.com")
    # ftbfsbug = bz.getbug("F33FTBFS")

    ftibug = bz.getbug("F33FailsToInstall")
    fti_report = {}
    # TODO: report obsoleted packages
    for src, pkg_rules in fti.items():
        problems = collections.defaultdict(list)
        for pkg, rules in pkg_rules.items():
            if re.search(r"^rust-.*-devel$", pkg):
                continue

            # All direct problems will be in the first rule
            for info in rules[0]:
                # TODO: add support for reporting conflicts and such
                if (
                    info["solvable"].name != pkg
                    or info["type"] != solv.Solver.SOLVER_RULE_PKG_NOTHING_PROVIDES_DEP
                ):
                    # Only interested in missing providers of a package itself
                    continue
                # Skip hacky multilib packages
                if "(x86-32)" in str(info["dep"]):
                    continue
                problems[pkg].append(info["str"])

        if problems:
            fti_report[src] = problems

    ftibug = bz.getbug("F33FailsToInstall")
    query_fti = bz.build_query(
        product="Fedora",
        include_fields=[
            "id",
            "status",
            "component",
            "creation_time",
            "assigned_to",
            "flags",
            "blocks",
        ],
    )
    query_fti["blocks"] = ftibug.id
    current_ftis = {b.component: b for b in bz.query(query_fti) if b.status != "CLOSED"}

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))

    fti_template = env.get_template("create-fti.j2")

    for src, pkgs in sorted(fti_report.items()):
        if src in current_ftis:
            print(
                f"Skipping {src} because bug already exists: {current_ftis[src].id}",
                file=sys.stderr,
            )
            continue

        description = fti_template.render(src=src, pkg_problems=pkgs)
        summary = f"F{release}FailsToInstall: {', '.join(pkgs)}"
        if len(summary) > 255:
            summary = f"F{release}FailsToInstall: Multiple packages built from {src}"
        create_fti_info = bz.build_createbug(
            product="Fedora",
            version="rawhide",
            component=src,
            summary=summary,
            description=description,
            blocks=ftibug.id,
        )
        print(description)
        bz.createbug(create_fti_info)

    fixed_ftis = {src: b for src, b in current_ftis.items() if src not in fti_report}
    if fixed_ftis:
        comment = env.get_template("close-fti.j2").render()
        close = bz.build_update(comment=comment, status="CLOSED", resolution="RAWHIDE")
        unblock = bz.build_update(comment=comment, blocks_remove=ftibug.id)
        to_close = [
            b.id
            for b in fixed_ftis.values()
            if not (set(b.blocks) - {ftibug.id}) & set(TRACKERS.values())
        ]
        to_unblock = [b.id for b in fixed_ftis.values() if b.id not in to_close]
        print(f"Closing FTI bugs for fixed components: {to_close}", file=sys.stderr)
        bz.update_bugs(to_close, close)
        print(
            f"Unblocking FTI tracker for fixed components: {to_unblock}",
            file=sys.stderr,
        )
        bz.update_bugs(to_unblock, unblock)
        current_ftis = {
            src: b for src, b in current_ftis.items() if src not in fixed_ftis
        }
    else:
        print("No FTI bugs to close, everything is still broken", file=sys.stderr)

    # Now we care only about bugs in NEW state
    current_ftis = {src: b for src, b in current_ftis.items() if b.status == "NEW"}
    for src, b in current_ftis.items():
        print(f"Checking {b.id} ({src})…")
        handle_orphaning(b)


if __name__ == "__main__":
    follow_policy()
