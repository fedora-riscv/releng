#!/bin/bash
#This whole script needs improvement, it is just a quick fix.


release=$1

mkdir -p /pub/fedora/linux/updates/$release/Everything/{aarch64,armhfp,x86_64}/{Packages,debug,drpms}
mkdir -p /pub/fedora/linux/updates/$release/Modular/{aarch64,armhfp,x86_64}/{Packages,debug,drpms}

mkdir -p /pub/fedora/linux/updates/$release/Everything/SRPMS/Packages
mkdir -p /pub/fedora/linux/updates/$release/Modular/SRPMS/Packages

mkdir -p /pub/fedora-secondary/updates/$release/Everything/{i386,ppc64le,s390x}/{Packages,debug,drpms}
mkdir -p /pub/fedora-secondary/updates/$release/Modular/{i386,ppc64le,s390x}/{Packages,debug,drpms}

for dir in /pub/fedora/linux/updates/$release/Everything/*
do
	createrepo_c $dir 
done

for dir in /pub/fedora/linux/updates/$release/Modular/*
do
	createrepo_c $dir
done

for dir in /pub/fedora-secondary/updates/$release/Everything/*
do
	createrepo_c $dir
done

for dir in /pub/fedora-secondary/updates/$release/Modular/*
do
	createrepo_c $dir
done


mkdir -p /pub/fedora/linux/updates/$release/Everything/source/tree/Packages
mkdir -p /pub/fedora/linux/updates/$release/Modular/source/tree/Packages

createrepo_c /pub/fedora/linux/updates/$release/Everything/source/tree
createrepo_c /pub/fedora/linux/updates/$release/Modular/source/tree

for dir in /pub/fedora/linux/updates/$release/Everything/*/debug/
do
	mkdir -p $dir/Packages
	createrepo_c $dir
done

for dir in /pub/fedora/linux/updates/$release/Modular/*/debug/
do
	mkdir -p $dir/Packages
	createrepo_c $dir
done

for dir in /pub/fedora-secondary/updates/$release/Everything/*/debug/
do
	mkdir -p $dir/Packages
	createrepo_c $dir
done

for dir in /pub/fedora-secondary/updates/$release/Modular/*/debug/
do
	mkdir -p $dir/Packages
	createrepo_c $dir
done

#Testing repos

mkdir -p /pub/fedora/linux/updates/testing/$release/Everything/{aarch64,armhfp,x86_64}/{Packages,debug,drpms}
mkdir -p /pub/fedora/linux/updates/testing/$release/Modular/{aarch64,armhfp,x86_64}/{Packages,debug,drpms}

mkdir -p /pub/fedora/linux/updates/testing/$release/Everything/SRPMS/Packages
mkdir -p /pub/fedora/linux/updates/testing/$release/Modular/SRPMS/Packages

mkdir -p /pub/fedora-secondary/updates/testing/$release/Everything/{i386,ppc64le,s390x}/{Packages,debug,drpms}
mkdir -p /pub/fedora-secondary/updates/testing/$release/Modular/{i386,ppc64le,s390x}/{Packages,debug,drpms}

for dir in /pub/fedora/linux/updates/testing/$release/Everything/*
do
	createrepo_c $dir 
done

for dir in /pub/fedora/linux/updates/testing/$release/Modular/*
do
	createrepo_c $dir
done

for dir in /pub/fedora-secondary/updates/testing/$release/Everything/*
do
	createrepo_c $dir
done

for dir in /pub/fedora-secondary/updates/testing/$release/Modular/*
do
	createrepo_c $dir
done


mkdir -p /pub/fedora/linux/updates/testing/$release/Everything/source/tree/Packages
mkdir -p /pub/fedora/linux/updates/testing/$release/Modular/source/tree/Packages

createrepo_c /pub/fedora/linux/updates/testing/$release/Everything/source/tree
createrepo_c /pub/fedora/linux/updates/testing/$release/Modular/source/tree

for dir in /pub/fedora/linux/updates/testing/$release/Everything/*/debug/
do
	mkdir -p $dir/Packages
	createrepo_c $dir
done

for dir in /pub/fedora/linux/updates/testing/$release/Modular/*/debug/
do
	mkdir -p $dir/Packages
	createrepo_c $dir
done

for dir in /pub/fedora-secondary/updates/testing/$release/Everything/*/debug/
do
	mkdir -p $dir/Packages
	createrepo_c $dir
done

for dir in /pub/fedora-secondary/updates/testing/$release/Modular/*/debug/
do
	mkdir -p $dir/Packages
	createrepo_c $dir
done
