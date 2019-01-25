# -*- mode: ruby -*-
# vi: set ft=ruby :
# SPDX-License-Identifier:    GPL-2.0+
# Authors:
#     Robert Marshall <rmarshall@redhat.com>

Vagrant.configure("2") do |config|
    config.vm.box = "fedora/29-cloud-base"

    config.vm.provision "shell", inline: <<-SHELL
        dnf update -y
        dnf install -y vim python3 fpaste
    SHELL
end
