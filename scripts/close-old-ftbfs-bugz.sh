#!/bin/bash
set -e
set -u
set -o pipefail

tracker=${1:-1750908}
dist=${1:-fc32}


for line in $(bugzilla query --blocked $tracker --status NEW --outputformat "%{id}@%{component}@%{creation_time}"); do
  line=( ${line/@/ } )
  bug=${line[0]}
  line=( ${line[1]/@/ } )
  component=${line[0]}
  creation_time=${line[1]}
  builds=$(koji list-builds --package $component --after "$creation_time" --state=COMPLETE --quiet) || continue
  # XXX any better way to filter builds by release?
  builds=$(echo "$builds" | grep "$dist " | cut -f1 -d' ' | tr '\n' ' ' || true)
  if ! [ -z "$builds" ]; then
    echo "$builds"
    bugzilla modify --status CLOSED --close NEXTRELEASE --comment "The following builds were made after this report was opened: $builds" $bug
  fi
done
