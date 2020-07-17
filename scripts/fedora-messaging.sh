# fedora-messaging.sh
#
# This is a bash shell script that is meant to be sourced by other scripts
# and aims to deliver functions common to sending messages to 
# fedora-messaging[0] in rel-eng shell scripts.
#
# [0] - https://github.com/fedora-infra/fedora-messaging


# NOTES:
#  FIXME: This might be obsolete:
#   - Scripts that source this should define at least the following:
#       FEDMSG_MODNAME
#       FEDMSG_CERTPREFIX
#
#       Example:
#
#           FEDMSG_MODNAME="compose"
#           FEDMSG_CERTPREFIX="bodhi"
#           source ./scripts/fedora-messaging.sh
#
#           fedmsg_json_start=$(printf '{"log": "start", "branch": "f24", "arch": "x86_64"}')
#           send_fedora_message "${fedmsg_json_start}" f24 start

# This uses the new fedora-messaging bus:
LOGGER=releng/scripts/fedora-messaging-logger

function send_fedora_message()
{
    jsoninput="${1}"
    dist="${2}"
    topic="${3}"

    echo ${jsoninput} | $LOGGER \
        --cert-prefix ${FEDMSG_CERTPREFIX} \
        --modname ${FEDMSG_MODNAME} \
        --topic ".${dist}.${topic}" \
        --json-input
}

