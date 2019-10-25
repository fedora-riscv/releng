# fedmsg-functions
#
# This is a bash shell script that is meant to be sourced by other scripts
# and aims to deliver functions common to sending messages to fedmsg[0]
# in rel-eng shell scripts.
#
# [0] - http://www.fedmsg.com/en/latest/


# NOTES:
#   - Scripts that source this should define at least the following:
#       FEDMSG_MODNAME
#       FEDMSG_CERTPREFIX
#
#       Example:
#
#           FEDMSG_MODNAME="compose"
#           FEDMSG_CERTPREFIX="bodhi"
#           source ./scripts/fedmsg-functions.sh
#
#           fedmsg_json_start=$(printf '{"log": "start", "branch": "f24", "arch": "x86_64"}')
#           send_fedmsg "${fedmsg_json_start}" f24 start

# This is the old fedmsg:
#LOGGER=fedmsg-logger

# This uses the new fedora-messaging bus:
LOGGER=./fedora-messaging-logger

function send_fedmsg()
{
    jsoninput="${1}"
    dist="${2}"
    topic="${3}"

    echo ${jsoninput} | $LOGGER \
        --cert-prefix ${FEDMSG_CERTPREFIX} \
        --modname ${FEDMSG_MODNAME} \
        --topic "${dist}.${topic}" \
        --json-input
}

