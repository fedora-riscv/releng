Sign the packages
-----------------

* This doc explains how to sign builds in the release(s).

* Manual signing should rarely ever be needed anymore. Just make sure that
  robosignatory is setup for all tags that are created.

* If a build seems to be stuck in the autosigning queue (one of the -pending or
  -signing-pending tags), just koji untag and koji tag the package. This will
  retrigger autosigning.

* If bodhi is reporting a build as unsigned but the build is not in the
  -signing-pending tag, that means bodhi missed the tagging. Just run the
  following command to make the build get retagged again, giving Bodhi another
  change at seeing the signing

  ::

    $ koji move $dist-updates-testing-pending $dist-signing-pending $build

 
* If need be, sign builds using scripts/sigulsign_unsigned.py from releng git repo

  *NOTE! This will NOT help if Bodhi marks a build as unsigned!*
 
  ::
 
    $ ./sigulsign_unsigned.py -vv --write-all \
        --sigul-batch-size=25 fedora-22 \
        $(cat /var/cache/sigul/Stable-F22 /var/cache/sigul/Testing-F22)
 
(Make sure you sign each release with the right key... ie, 'fedora-19' key
with F19 packages, or 'epel-6' with EL-6 packages)
