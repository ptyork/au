# Assignment Workflows Overview

These tools and the workflows and best practices described herein are
intentionally "opinionated". GitHub Classroom is nearly as flexible as Git
itself. Many choices must be made in order to leverage it most effectively.

Choices involve features of Classroom that simply go unused as well as
assumptions and suggestions regarding assignment structure, way they are
evaluated, and the way feedback is provided to students.

Suggested workflows specific to particular types of assignments are covered on
separate pages:

  * [Common Assignment Workflow](common.md) - processes related to GitHub,
    GitHub Classroom, and GitHub Codespaces that are common to all assignments.
  * [Python Assignment Workflow](python.md) - processes specific to Python
    programming assignments.
  * [SQL Assignment Workflow](sql.md) - processes specific to MySQL /
    MariaDB SQL query and database design assignments.

## "Work Locally" Philosophy



## Unused GitHub Classroom Features

At this time the following GitHub Classroom features are not recommended:

  - **Feedback Pull Requests:**
    
    This feature has is simply too confusing for students (and most instructors
    for that matter) in all but the most advanced technical courses. Since
    instructors are owners of student repositories, it is easier and less
    problematic simply to merge and commit feedback directly.

  - **Autograding with GitHub Actions**

    This can certainly still be used. However, we've encountered issues that are
    difficult to diagnose and often impossible to fix. The student feedback is
    also somewhat confusing for less advanced students and is likewise difficult
    to customize. Instead we embrace interactive automation for grading and
    feedback that does not involve GitHub actions.

We do 