Sign the packages
-----------------

* This doc explains how to sign builds in the release(s).
 
* Sign builds using scripts/sigulsign_unsigned.py from releng git repo
 
  ::
 
    $ ./sigulsign_unsigned.py -vv --write-all \
        --sigul-batch-size=25 fedora-22 \
        $(cat /var/cache/sigul/Stable-F22 /var/cache/sigul/Testing-F22)
 
(Make sure you sign each release with the right key... ie, 'fedora-19' key
with F19 packages, or 'epel-6' with EL-6 packages)

Here is another example, inside a loop:

::

    for i in 24 23 22;
    do
        ~/releng/scripts/sigulsign_unsigned.py \
            fedora-$i -v --write-all \
            --sigul-batch-size=25 $(cat /var/cache/sigul/{Stable,Testing}-F${i});
    done

    for i in 7 6;
    do
        ~/releng/scripts/sigulsign_unsigned.py \
            epel-$i -v --write-all \
            --sigul-batch-size=25 $(cat /var/cache/sigul/{Stable,Testing}-*EL-${i});
    done


* If signing process struggles to finish, then consider adjusting the
  ``--sigul-batch-size=N`` to ``1``, which is more resilient but much slower.
