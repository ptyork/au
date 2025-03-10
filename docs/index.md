# `au` - GitHub Classroom Automation Tools

The gold standard for managing GitHub Classroom assignments at scale. These
tools help to automate the workflows required to create, administer, evaluate,
and provide feedback for assignments.

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
