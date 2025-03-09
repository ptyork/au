# AU Command Line Reference

This page provides documentation for the `au` command line tool. This tool
should be available on all platforms after installation.

Most of the commands assume that you will specify either a ROOT_DIR (most will
be the directory into which you will clone or have cloned all student assignment
repositories) or a STUDENT_DIR (one student assignment repository). In most
cases, if you leave off this argument, the tools assume that you intend to treat
the present working directory as the ROOT_DIR or STUDENT_DIR.

Note also that to prevent unintentional loss of work, by default the tools will
not overwrite any potentially modified directories or files. You will be given
the opportunity to force changes, but the default is to be non-destructive.
Likewise, prior to potentially long tasks, by default the tool will prompt for
confirmation. This too can be overridden if and as needed.

The tools are intended primarily to be run interactively and thus will prompt
for missing information. However, it is possible to pass all required arguments
and options from the command line if batch / unattended operation is desired.

::: mkdocs-click
    :module: au.cli.classroom
    :command: classroom
    :prog_name: au classroom
    :list_subcommands: true
    :depth: 1

::: mkdocs-click
    :module: au.cli.python
    :command: python
    :prog_name: au python
    :list_subcommands: true
    :depth: 1

::: mkdocs-click
    :module: au.cli.sql
    :command: sql
    :prog_name: au sql
    :list_subcommands: true
    :depth: 1
    