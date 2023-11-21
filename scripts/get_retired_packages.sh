#!/usr/bin/bash

set -u

declare -a active_branches=( rawhide )
declare -a releases=( current pending frozen )
declare -A retired
declare -a git_branches
declare -r checkout_path="${1:-/srv/git/rpms}"

# Get active releases from bodhi and store them in an array
for release in ${releases[@]}; do
  active_branches=("$active_branches $(curl -X GET -s -H 'Accept: application/json' 'https://bodhi.fedoraproject.org/releases/?state='$release | jq -r '[ .releases[].branch | select(test("\\d+$"))] | unique | .[]')")
done


for git_repo in ${checkout_path}/*.git; do
  # Declare these helper arrays inside the loop
  declare -a branch_intersection=()
  declare -a unicorn=()
  # pushd popd can be silenced, depends on if we want to see whether the desired path is correct
  pushd $git_repo
  # Get the name of the package
  package=$(basename $git_repo .git)
  # Get the branches of the git repo, to check only in thse that exist, to avoid git fatal errors
  git_branches=($(git branch | cut -c 3-))

  # Create intersection of the active releases and the git branches to avoid git fatal errors
  for release in ${active_branches[@]}; do
    for branch in "${git_branches[@]}"; do
      if [[ $release == $branch ]]; then
        branch_intersection+=("$release")
      fi
    done
  done

  # Deduplicate the branch array
  unicorn=($(printf "%s\n" "${branch_intersection[@]}" | sort -u))
  
  # Check for presence of a dead.package (indicates retired package)
  for release in ${unicorn[@]}; do
    if [[ -n "$(git ls-tree ${release} --name-only -- dead.package)" ]]; then
      echo "$package is retired"
      # Add retired package to an associative array as a value under a key that represents release
      retired["$release"]+="\"$package\","
    fi
  done
  popd
done

# Store the retired packages in separate json files by release
for release in "${!retired[@]}"; do
  printf '{"%s": [%s]}\n' "$release" "${retired[$release]:0:-1}" > /srv/cache/lookaside/retired_in_${release}.json
done
