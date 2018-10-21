import configparser
import bugzilla
import pathlib
import sys
from click import progressbar
import logging

import massrebuildsinfo

assert sys.version_info[0] > 2, 'Needs Python 3'

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
fh = logging.FileHandler('bugzilla.log')
fh.setLevel(logging.DEBUG)
LOGGER.addHandler(fh)


# get the latest Fedora version and tracking bug
for key, value in massrebuildsinfo.MASSREBUILDS.items():
    fedora = key.upper()
    tracking = value['tracking_bug']
    break

# Get credentials from config
config_path = pathlib.Path('./ftbfs.cfg')
if not config_path.exists():
    config_path = pathlib.Path('/etc/ftbfs.cfg')
if not config_path.exists():
    raise RuntimeError('Create a config file as ./ftbfs.cfg or /etc/ftbfs.cfg')

config = configparser.ConfigParser()
config.read(config_path)

URL = config['bugzilla'].get('url', 'https://bugzilla.redhat.com')
USERNAME = config['bugzilla']['username']
PASSWORD = config['bugzilla']['password']
FEDORA = config['bugzilla'].get('fedora', fedora)
TRACKING = config['bugzilla'].get('tracking', tracking)


TEMPLATE = f"""Dear Maintainer,

your package has not been built successfully in {FEDORA}. Action is required from you.

If you can fix your package to build, perform a build in koji, and either create
an update in bodhi, or close this bug without creating an update, if updating is
not appropriate [1]. If you are working on a fix, set the status to ASSIGNED to
acknowledge this. Following the latest policy for such packages [2], your package
can be orphaned if this bug remains in NEW state more than 8 weeks.

[1] https://fedoraproject.org/wiki/Updates_Policy
[2] https://docs.fedoraproject.org/en-US/fesco/Fails_to_build_from_source_Fails_to_install/
"""  # noqa

cache_dir = pathlib.Path('~/.cache/FTBFS_weekly_reminder/').expanduser()
cache_dir.mkdir(exist_ok=True)
ALREADY_FILED = cache_dir / 'ALREADY_FILED'

bzapi = bugzilla.Bugzilla(URL, user=USERNAME, password=PASSWORD)

failed = []
updated = []


def new_ftbfs_bugz(tracker=TRACKING, version='29'):
    query = bzapi.build_query(product='Fedora', status='NEW', version=version)
    query['blocks'] = tracker
    return bzapi.query(query)


def needinfo(requestee):
    return {
        'name': 'needinfo',
        'requestee': requestee,
        'status': '?',
    }


def send_reminder(bug, comment=TEMPLATE):
    flags = [needinfo(bug.assigned_to)]
    update = bzapi.build_update(comment=comment, flags=flags)
    try:
        bzapi.update_bugs([bug.id], update)
    except Exception:
        LOGGER.exception(bug.weburl)
        failed.append(bug)
    else:
        updated.append(bug)
        with open(ALREADY_FILED, 'a') as f:
            print(bug.id, file=f)


if ALREADY_FILED.exists():
    print(f'Loading bug IDs from {ALREADY_FILED}. Will not fill those. '
          f'Remove {ALREADY_FILED} to stop this from happening.')
    ignore = [
        int(line.rstrip()) for line in ALREADY_FILED.read_text().splitlines()
    ]
else:
    ignore = []


print('Gathering bugz, this can take a while...')

bugz = new_ftbfs_bugz()

print(f'There are {len(bugz)} NEW bugz, will send a reminder')
if ignore:
    print(f'Will ignore {len(ignore)} bugz from {ALREADY_FILED}')
    print(f'Will update {len(set(b.id for b in bugz) - set(ignore))} bugz')


def _item_show_func(bug):
    if bug is None:
        return 'Finished!'
    return bug.weburl


with progressbar(bugz, item_show_func=_item_show_func) as bugbar:
    for bug in bugbar:
        if bug.id not in ignore:
            send_reminder(bug)

print(f'Updated {len(updated)} bugz')

if failed:
    print(f'Failed to update {len(failed)} bugz', file=sys.stderr)
    for bug in failed:
        print(bug.weburl, file=sys.stderr)
    sys.exit(1)
elif ALREADY_FILED.exists():
    target = ALREADY_FILED.parent / f'~{ALREADY_FILED.name}'
    print(f'Moving {ALREADY_FILED} to {target}, all bugz filed')
    ALREADY_FILED.rename(target)
