# `au` - GitHub Classroom Automation Tools

Solid gold tools for automating much of the workflow involved in managing and
evaluating assignments using GitHub Classroom.

## Purpose

GitHub Classroom, especially when combined with GitHub Codespaces, can transform
the way instructors deliver technology-focused assignments, evaluate them, and
provide feedback to students. However, there is a huge learning curve for most
instructors to be able to use these tools effectively. Likewise, the process can
involve a lot of repetitive and error-prone steps, even with basic automation
tools.

This package contains a number of resources to ease the burden of instructors
using GitHub Classroom.

 - `au` is a commandline tool designed to automate many of the core workflows
   involved in creating and evaluating assignments.
 - `checkit` is a separately installable commandline tool for students to use to
   test their own assignments against all or a subset of the automated tests
   used by the instructor for evaluation. (**_coming soon_**)
 - `au_unit` is a separately installable Python module that provides useful
   tools to help with the creatinon of unit test for use in student assignment
   evaluation. (**_coming soon_**)
 - "Opinionated" workflow suggestions to help with assignment creation,
   automated test creation, semi-automated assignment evaluation, and feedback.
   (**_evolving_**)
 - Example assignment configurations that can be used to better understand the
   above workflows and adapted to meet specific assignment needs.

At present, bespoke tooling is available to support:

  - Python programming assignments
  - SQL programming assignments with MySQL / MariaDB (**_coming soon_**)

## Usage

Click to [read the full documentation](https://ptyork.github.io/au/).

## Installation

At present, the only way to install the project is using Python's pip installer:
```
pip install au-tools
```
or
```
pip3 install au-tools
```
The tools will make heavy use of both the `git` (Git) and the `gh` (GitHub)
command line tools. Both must be installed and authenticated prior to use.

For more details read the [installation guide](https://ptyork.github.io/au/install/).

