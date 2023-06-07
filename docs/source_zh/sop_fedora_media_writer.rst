.. SPDX-License-Identifier:    CC-BY-SA-3.0


========================================
Fedora Media Writer构建和签名
========================================

说明
===========
每当有新版本的 Fedora Media Writer 可用时，都需要对其进行构建和代码签名。

操作
======

Windows
-------

#. 从私有 ansible repository 获得 Windows 代码签名密钥。它位于 ansible-private/files/code-signing/ 目录中


#. 将 .cert 格式的证书转换为 .pxf 格式：


   ::
   
        $ openssl pkcs12 -export -in code-signing.crt -inkey code-signing.key -out authenticode.pfx


#. 克隆 Fedora Media Writer git repo:

   ::

        $ git clone https://github.com/MartinBriza/MediaWriter.git

#. Checkout 到要为其创建可执行文件的版本标签：

   ::

        $ git checkout tags/<release_number>

#. 用于生成可执行文件并对其进行签名的脚本可在 dist/win/build.sh 中找到
 
#. 从 koji 获取 mingw-mediawriter 。确保版本是需要构建和签名的版本。

#. 安装 build.sh 脚本中 PACKAGES 变量下列出的其余软件包。

#. 将 CERTPATH 导出到 .pfx 文件所在的位置，并确保将其命名为 authenticode.pfx ，并将 CERTPASS 导出到包含用于创建 .pvk 文件密码的文件。

#. 运行 build.sh 脚本：

   ::

        $ ./build.sh

验证
============
FedoraMediaWriter-win32-<release_number>.exe 位于 dist/win/ 目录下。

OS X：
---------

构建：
------

#. 从 apple store 中安装 xcode 8.1。
#. 从以下位置安装 qt for mac：
       http://download.qt.io/official_releases/qt/5.7/5.7.0/qt-opensource-mac-x64-clang-5.7.0.dmg
#. 打开终端并运行以下命令
 
   ::
        $ git clone https://github.com/MartinBriza/MediaWriter
        $ cd MediaWriter
        $ mkdir build
        $ cd build
        $ $QT_PREFIX/$QT_VERSION/clang64/bin/qmake ..
        $ make
        $ cp build/helper/mac/helper.app/Contents/MacOS/helper build/app/Fedora\ Media\ Writer.app/Contents/MacOS/
        $ cd build/app
        $ $QT_PREFIX/$QT_VERSION/clang_64/bin/macdeployqt "Fedora Media Writer.app" \
        -executable="Fedora Media Writer.app/Contents/MacOS/helper" -qmldir="../../app"

准备证书
--------------------

这只需要在每台构建计算机上执行一次，并通过从 Apple 请求证书来准备证书。

#. 从 Mac App store 安装 Xcode
#. 启动 Xcode
#. 按 Command- 键（或在菜单栏中点按 Xcode -> Preferences）
#. 转到 Accounts 选项卡
#. 单击加号按钮并登录
#. 选择新账户
#. 选择正确的团队
#. 点击查看详细信息
#. 在 “Signing Identities” 下找到 “Developer ID Application”
#. 点击创建
#. 等到按钮消失
#. 完成

签名和 DMG
------------

#. 打开终端
#. cd 到 FMW 项目的根目录
#. 运行以下 bash 脚本：

      ::

         #/bin/bash

         security -v unlock-keychain login.keychain

         # First sign all dynamic libraries (dylib's)
         cd "build/app/Fedora Media Writer.app"
         for dylib in $(find  . -name "*dylib")
         do
         codesign -s "Developer ID Application: Fedora Gilmore" -v $dylib
         done
         # Now sign framework bundles
         for framework in $(find  . -name "*framework")
         do
         codesign -s "Developer ID Application: Fedora Gilmore" -v $framework
         done

         # Sign the two binaries
         codesign -s "Developer ID Application: Fedora Gilmore" -v Contents/MacOS/helper
         codesign -s "Developer ID Application: Fedora Gilmore" -v "Contents/MacOS/Fedora Media Writer"

         # Sign the app bundle
         codesign -s "Developer ID Application: Fedora Gilmore" -v .

         # Create the dmg
         cd ..
         rm -f FedoraMediaWriter-osx-*.dmg

         hdiutil create -srcfolder "Fedora Media Writer.app"  -format UDCO -imagekey zlib-level=9 -scrub \
                        -volname FedoraMediaWriter-osx FedoraMediaWriter-osx-$(git  describe --tags).dmg

帐户电子邮件(OS X)
-------------------

      ::
         releng@fedoraproject.org

帐户持有人(OS X)
---------------------

#. 主要: Dennis Gilmore(ausil)
#. 备份: Kevin Fenzi(kevin)
#. 经理/账单支付人: Paul Frields(pfrields)


将二进制文件同步到web
========================
将这两个文件复制到 sundries01 上的 /srv/web/fmw 目录中，并创建指向 FedoraMediaWriter-win32-latest.exe 和 FedoraMediaWriter-osx-latest.dmg 的符号链接。

运行之前考虑
=======================
目前尚无。

签名问题
=======================
如果构建已完成但未签名，请尝试编辑 ``build.sh`` 并为所有 osslsigncode 命令添加 -askpass 参数并运行脚本，当它要求输入密码时，您可以输入用于创建 .pvk 文件的密码。
