.. SPDX-License-Identifier:    CC-BY-SA-3.0


.. _sop:

============================
Fedora发行版工程标准操作程序
============================

本页介绍Fedora发布工程的标准操作流程。

目的
====
SOP部分包含Fedora Release Engineering团队为项目提供的任务列表。当前的Fedora发行版工程团队成员可以添加他们知道的任务，列出完成任务的步骤以及要考虑的问题。这是个很好的方法，确保个人并不是唯一能够解决问题的人。

社区
====
SOP部分留给公众，因为我们希望社区中的其他人会添加常见问题，修复我们的步骤，总的来说检查我们在做什么，并在我们做傻事时帮助我们。
我们鼓励任何有兴趣的人仔细梳理我们的流程。我们可能会在这个过程中学到一些东西，这会让我们变得更好。因此，请打开一个 `pull request`_ 提出改进建议。


程序
====

需要：
#. 正在编写一个正式版本
#. 公开发布合成版本

标准操作程序
============

.. toctree::
    :maxdepth: 2

    sop_adding_build_targets
    sop_adding_content_generator
    sop_adding_new_release_engineer
    sop_adding_new_branch_sla
    sop_adding_packages_compose_artifact
    sop_adding_side_build_targets
    sop_branch_freeze
    sop_branching
    sop_breaking_development_freeze
    sop_composing_fedora
    sop_clean_amis
    sop_create_release_signing_key
    sop_deprecate_ftbfs_packages
    sop_end_of_life
    sop_eol_change
    sop_mass_branching
    sop_bodhi_activation
    sop_mass_rebuild_packages
    sop_mass_rebuild_modules
    sop_file_ftbfs
    sop_generating_openh264_composes
    sop_package_blocking
    sop_package_unblocking
    sop_process_dist_git_requests
    sop_promoting_container_content
    sop_signing_builds
    sop_pushing_updates
    sop_release_package_signing
    sop_remote_dist_git_branches
    sop_requesting_task_automation_users
    sop_retire_orphaned_packages
    sop_sigul_client_setup
    sop_stage_final_release_for_mirrors
    sop_unretire
    sop_update_critpath
    sop_update_releng_docs
    sop_updating_comps
    sop_fedora_media_writer
    sop_find_module_info
    sop_release_container_base_image

.. _pull request: https://pagure.io/releng/pull-requests
