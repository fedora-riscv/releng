.. SPDX-License-Identifier:    CC-BY-SA-3.0


========================
删除 dist-git 分支
========================

说明
===========
维护人员经常要求发布工程删除 dist-git 中的分支。

操作
======
#. 登录 batcave01

   ::

        ssh <fas-username>@batcave01.iad2.fedoraproject.org

#. 获取 root shell

#. 登录 pkgs01.iad2.fedoraproject.org
   ::

        ssh pkgs01.iad2.fedoraproject.org

#. 切换到包的目录

   ::

        cd /srv/git/rpms/<package>.git/

#. 删除分支

   ::

        git branch -D <branchname> </pre>

验证
============
要验证，只需列出分支。

::

    git branch

运行之前考虑
=======================
确保有问题的分支不是我们预先创建的分支之一
``f??/rawhide`` ， ``olpc?/rawhide`` ， ``el?/rawhide``
