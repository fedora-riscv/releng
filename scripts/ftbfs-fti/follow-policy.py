#!/usr/bin/python3

import collections
import datetime
import os
import re
import sys

import bugzilla
import click
import jinja2
import requests
import solv

TEMPLATE_DIR = os.path.dirname(os.path.realpath(__file__))

NOW = datetime.datetime.now(datetime.timezone.utc)
TRACKERS = {
    "F31FailsToInstall": 1700324,
    "F32FailsToInstall": 1750909,
    "F33FailsToInstall": 1803235,
    "F34FailsToInstall": 1868279,
    "F31FTBFS": 1700317,
    "F32FTBFS": 1750908,
    "F33FTBFS": 1803234,
    "F34FTBFS": 1868278,
}
RAWHIDE = "34"


def _bzdate_to_python(date):
    return datetime.datetime.strptime(str(date), "%Y%m%dT%H:%M:%S").replace(
        tzinfo=datetime.timezone.utc
    )


def handle_orphaning(bug, tracker):
    bz = bug.bugzilla

    history = bug.get_history_raw()["bugs"][0]["history"]

    try:
        start_time = _bzdate_to_python(
            next(
                u["when"]
                for u in history
                for c in u["changes"]
                if c["field_name"] == "blocks"
                and str(tracker.id) in {b.strip() for b in c["added"].split(",")}
            )
        )
    except StopIteration:
        start_time = _bzdate_to_python(bug.creation_time)
    diff = NOW - start_time
    if diff < datetime.timedelta(weeks=1):
        print(
            f"→ Week did not pass since bug started to block tracker ({start_time}), skipping…",
        )
        return

    # Only reliable way to get whether needinfos were set is go through history
    needinfos = [
        u
        for u in history
        for c in u["changes"]
        if f"needinfo?({bug.assigned_to})" in c["added"]
    ]
    bzupdate = None
    flag = {"name": "needinfo", "status": "?", "requestee": bug.assigned_to}
    if not needinfos:
        print("Asking for the first needinfo")
        bzupdate = bz.build_update(
            comment="""Hello,

This is the first reminder (step 3 from https://docs.fedoraproject.org/en-US/fesco/Fails_to_build_from_source_Fails_to_install/#_package_removal_for_long_standing_ftbfs_and_fti_bugs).

If you know about this problem and are planning on fixing it, please acknowledge so by setting the bug status to ASSIGNED. If you don't have time to maintain this package, consider orphaning it, so maintainers of dependent packages realize the problem.""",
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
                f"→ Week did not pass since first needinfo ({_bzdate_to_python(needinfos[0]['when'])}), skipping…",
            )
            return
        try:
            needinfo_after_four_weeks = next(
                _bzdate_to_python(n["when"])
                for n in needinfos
                if _bzdate_to_python(n["when"]) - needinfo_after_week
                >= datetime.timedelta(weeks=3)
            )
            if NOW - needinfo_after_four_weeks >= datetime.timedelta(weeks=4):
                print("Opening releng ticket")
                print(f' * `{bug.component}` ([bug](https://bugzilla.redhat.com/show_bug.cgi?id={bug.id}))', file=sys.stderr)
            else:
                print(
                    f"→ 4 weeks did not pass since second needinfo ({needinfo_after_four_weeks}), skipping…",
                )
                return
        except StopIteration:
            if NOW - needinfo_after_week >= datetime.timedelta(weeks=3):
                print("Asking for another needinfo")
                bzupdate = bz.build_update(
                    comment="""Hello,

This is the second reminder (step 4 from https://docs.fedoraproject.org/en-US/fesco/Fails_to_build_from_source_Fails_to_install/#_package_removal_for_long_standing_ftbfs_and_fti_bugs).

If you know about this problem and are planning on fixing it, please acknowledge so by setting the bug status to ASSIGNED. If you don't have time to maintain this package, consider orphaning it, so maintainers of dependent packages realize the problem.""",
                    flags=[flag],
                )
            else:
                print(
                    f"→ 3 weeks did not pass since first needinfo ({needinfo_after_week}), skipping…",
                )
                return

    if bzupdate is not None:
        result = bz.update_bugs([bug.id], bzupdate)
        if "flags" in bzupdate and not result["bugs"][0]["changes"]:
            # FIXME: Probably bug(s) in bugzilla and should be reported there
            # 1. Accounts which change email do not force needinfo change
            # 2. RHBZ can have multiple flags of the same type, but python-bugzilla does not like it much
            #    https://github.com/python-bugzilla/python-bugzilla/issues/118
            flags = bzupdate["flags"]
            flags_to_unset = [
                f for f in bug.flags if f["name"] in set(f["name"] for f in flags)
            ]
            flags = [f for f in bug.flags if f["name"] == "needinfo"]
            if not flags_to_unset:
                raise AssertionError(
                    "Flags update did not happen, neither there are flags to remove"
                )
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
            # Retry setting a flag
            bz.update_bugs([bug.id], bz.build_update(flags=bzupdate["flags"]))


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
@click.option(
    "--release",
    type=click.Choice(sorted(set(t[1:3] for t in TRACKERS.keys()))),
    default="34",
    show_default=True,
    help="Fedora release",
)
def follow_policy(release):
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
    # ftbfsbug = bz.getbug(f"F{release}FTBFS")

    ftibug = bz.getbug(f"F{release}FailsToInstall")
    fti_report = {}
    # TODO: report obsoleted packages
    for src, pkg_rules in fti.items():
        problems = collections.defaultdict(list)
        for pkg, rules in pkg_rules.items():
            if re.search(r"^rust-.*-devel$", pkg) and int(release) < 34:
                continue
            if pkg.startswith("dummy-test-package"):
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
                if (
                    "(x86-32)" in str(info["dep"])
                    or "dssi-vst-wine" in str(info["dep"])
                    or "lmms-vst" in str(info["dep"])
                ):
                    continue
                problems[pkg].append(info["str"])

        if problems:
            fti_report[src] = problems

    pkg_owners = requests.get(
        "https://src.fedoraproject.org/extras/pagure_poc.json"
    ).json()

    ftibug = bz.getbug(f"F{release}FailsToInstall")
    query_fti = bz.build_query(
        product="Fedora",
        include_fields=[
            "id",
            "status",
            "component",
            "assigned_to",
            "flags",
            "blocks",
            "creation_time",
        ],
    )
    query_fti["blocks"] = ftibug.id
    current_ftis = {b.component: b for b in bz.query(query_fti)
                    if b.status != "CLOSED" and b.component != 'distribution'}

    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))
    env.globals["release"] = release

    fti_template = env.get_template("create-fti.j2")

    for src, pkgs in sorted(fti_report.items()):
        if src in current_ftis:
            print(
                f"Skipping {src} because bug already exists: {current_ftis[src].id}",
            )
            continue

        if pkg_owners["rpms"][src]["fedora"] == "orphan":
            # Skip reporting bugs for orphaned packages
            continue

        description = fti_template.render(src=src, pkg_problems=pkgs)
        summary = f"F{release}FailsToInstall: {', '.join(pkgs)}"
        if len(summary) > 255:
            summary = f"F{release}FailsToInstall: Multiple packages built from {src}"
        bz_version = release if release != RAWHIDE else "rawhide"
        create_fti_info = bz.build_createbug(
            product="Fedora",
            version=bz_version,
            component=src,
            summary=summary,
            description=description,
            blocks=ftibug.id,
        )
        print(description)
        bz.createbug(create_fti_info)

    fixed_ftis = {src: b for src, b in current_ftis.items() if src not in fti_report}
    # Ignore bugs which have pending updates in Bodhi
    for src, b in list(fixed_ftis.items()):
        if b.status not in {"MODIFIED", "ON_QA"}:
            continue
        print(
            f"Checking {b.id} if it was submitted as an update to appropriate release",
        )
        comments = b.getcomments()
        try:
            next(
                c
                for c in comments
                if c["creator"] == "updates@fedoraproject.org"
                and f"Fedora {release}" in c["text"]
            )
            print(f"Bug for {src} ({b.id}) has a pending update, ignoring")
            del fixed_ftis[src]
        except StopIteration:
            pass
    if fixed_ftis:
        comment = env.get_template("close-fti.j2").render()
        close = bz.build_update(
            comment=comment, status="CLOSED", resolution="WORKSFORME"
        )
        unblock = bz.build_update(comment=comment, blocks_remove=ftibug.id)
        unblock["minor_update"] = True
        to_close = [
            b.id
            for b in fixed_ftis.values()
            if not (set(b.blocks) - {ftibug.id}) & set(TRACKERS.values())
        ]
        to_unblock = [b.id for b in fixed_ftis.values() if b.id not in to_close]
        if to_close:
            print(f"Closing FTI bugs for fixed components: {to_close}")
            bz.update_bugs(to_close, close)
        if to_unblock:
            print(f"Unblocking FTI tracker for fixed components: {to_unblock}")
            bz.update_bugs(to_unblock, unblock)
        current_ftis = {
            src: b for src, b in current_ftis.items() if src not in fixed_ftis
        }
    else:
        print("No FTI bugs to close, everything is still broken")

    # Update bugs for orphaned packages
    orphaned = {
        src: b
        for src, b in current_ftis.items()
        if pkg_owners["rpms"][src]["fedora"] == "orphan"
    }
    for src, b in orphaned.items():
        click.echo(f"Checking if need to send notice to the orphaned package: {src} ({b.id})")
        comments = b.getcomments()
        update = False
        try:
            next(c for c in comments if "This package has been orphaned." in c["text"])
            continue
        except StopIteration:
            pass

        bz.update_bugs(
            [b.id],
            bz.build_update(
                comment=f"""This package has been orphaned.

You can pick it up at https://src.fedoraproject.org/rpms/{src} by clicking button "Take". If nobody picks it up, it will be retired and removed from a distribution.""",
                status="NEW",
            ),
        )

    # Now we care only about bugs in NEW state
    current_ftis = {
        src: b
        for src, b in current_ftis.items()
        if b.status == "NEW" and src not in orphaned
    }
    for src, b in current_ftis.items():
        print(f"Checking {b.id} ({src})…")
        handle_orphaning(b, ftibug)


if __name__ == "__main__":
    follow_policy()
