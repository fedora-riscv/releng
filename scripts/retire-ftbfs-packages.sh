#!/bin/bash
set -e
set -u
set -o pipefail

tracker=${1:-1674516}
date="${2:-2019-01-31 10:10:00.000000}"

export GIT_SSH=/usr/local/bin/relengpush

for line in $(bugzilla query --blocked $tracker --status NEW,ASSIGNED,POST,MODIFIED --outputformat "%{id}:%{component}"); do
  bug_component=( ${line/:/ } )
  bug=${bug_component[0]}
  component=${bug_component[1]}
  builds=$(koji list-builds --package $component --after "$date" --state=COMPLETE --quiet) || continue
  # XXX any better way to get rid of epel and fc29 builds?
  builds=$(echo "$builds" | egrep "fc(30|31)" | cut -f1 -d' ' | tr '\n' ' ' || true)
  if [ -z "$builds" ]; then
    echo "$component fails to build from source: https://bugzilla.redhat.com/show_bug.cgi?id=$bug"
    fedpkg --user releng clone $component
    (cd $component && git config user.name 'Fedora Release Engineering' && git config user.email 'releng@fedoraproject.org' && fedpkg --user releng retire "$component fails to build from source: https://bugzilla.redhat.com/show_bug.cgi?id=$bug")
    rm -rf $component
    bugzilla modify --status CLOSED --close EOL --comment "The package was retired." $bug
  else
    echo "The following builds were made: $builds"
    bugzilla modify --status CLOSED --close WORKSFORME --comment "The following builds were made: $builds" $bug
  fi
done
