对包进行签名
-----------------

* 本文档介绍如何在发布版本中对构建进行签名。

* 很少需要手动签名了。只需确保为创建的所有标签设置了自动化签名。

* 如果构建似乎卡在自动签名队列中（ -pending 或
  -signing-pending tags 标记之一），只需 koji 取消标记和重新标记包。这将重新触发自动签名。

* 如果Bodhi报告某个构建未签名，但该构建不在
  -signing-pending 标记中，则意味着Bodhi错过了标记。只需运行以下命令，让该构建重新标记，让Bodhi再次尝试查看签名：

  ::

    $ koji move $dist-updates-testing-pending $dist-signing-pending $build

 
* 如果需要，请使用 releng git 存储库中的 scripts/sigulsign_unsigned.py 对构建进行签名

  *注意！如果 Bodhi 将构建标记为未签名，这将不会生效！*
 
  ::
 
    $ ./sigulsign_unsigned.py -vv --write-all \
        --sigul-batch-size=25 fedora-22 \
        $(cat /var/cache/sigul/Stable-F22 /var/cache/sigul/Testing-F22)
 
（确保使用正确的密钥对每个发行版进行签名，例如对于F19软件包，使用“fedora-19”密钥进行签名，而对于EL-6软件包，则使用“epel-6”密钥进行签名。）
