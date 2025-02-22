#!/usr/bin/env python3

from typing import Dict, List

import click
from yaspin import yaspin

import sys
import re
from io import TextIOWrapper
from pathlib import Path
from pprint import pformat

from au.lib.common.csv import dict_from_csv
from au.lib.common.terminal import draw_double_line, draw_single_line
from au.lib.classroom import Assignment, Classroom
from au.lib.classroom import choose_assignment, choose_classroom, get_accepted_assignments, get_assignment
from au.lib.git import GitRepo

import logging
logger = logging.getLogger(__name__)

@click.command('clone-submissions')
@click.argument("root_dir",
                type=click.Path(exists=True,file_okay=False,dir_okay=True,readable=True,resolve_path=True,path_type=Path))
@click.option("-a", "--assignment-id", type=int,
              help="the integer classroom id for the assignment; will prompt for the classroom and assignment if not provided")
@click.option("--roster", type=click.File(),
              help="A GitHub Classroom roster file (usually named `classroom_roster.csv`. If provided, directories will be named using the associated student name as well as the student's GitHub login name.")
@click.option("-rp","--remove-prefix", is_flag=True, help="set to remove any prefix (slug) string common to all repositories")
@click.option("-u", "--update", is_flag=True, help="set to pull changes to existing repositories")
@click.option("-d", "--debug", is_flag=True, help="set to enable detailed output")
@click.option("-q", "--quiet", is_flag=True, help="set to reduce output to errors only")
@click.option("-p", "--preview", is_flag=True, help="set to show changes without actually making them")
def clone_submissions_cmd(root_dir: Path,
                          assignment_id: int = None,
                          roster: TextIOWrapper = None,
                          remove_prefix: bool = False,
                          update: bool = False,
                          debug: bool = False,
                          quiet: bool = False,
                          preview: bool = False):
    '''
    Clone all student repositories for a GitHub Classroom assignment into
    ROOT_DIR.

    \b Required Argument:
      ROOT_DIR
        the base directory into which assignmetns will be cloned.

    This command will use the specified|selected assignment to query GitHub
    Classroom for all accepted assignments. For each, it will run the following
    logic:

    \b
        if repository directory exists in ROOT_DIR
            if update flag is set
                pull updates from GitHub
            else
                skip
        else
            if repository has submissions
                clone repository into ROOT_DIR
            else
                skip

    By default, repositories will be named as they are in GitHub. However, to
    assist with sorting and identification, two additional options are provided.

    If a GitHub Classroom roster is provided using the --roster option and a
    student name match can be found in the roster, then the directory will be
    named as follows:

        [prefix][student_name]@[login_name]

    All commas, spaces, and invalid characters in the student name will be
    replaced with underscores. for example:
    
        hw1-York_Paul@ptyork
    
    If the --remove-prefix then the prefix (also called 'slug') will be removed
    from all assignments, whether or not a roster has been provided. So
    directory names will either be named:

        [login_name]
    
    or:
    
        [student_name]@[login_name]
    '''
    logging.basicConfig()

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.WARNING)
    else:
        logging.getLogger().setLevel(logging.INFO)

    # process roster to get mapping of id's to students
    id_student_map = None
    if roster:
        try:
            id_student_map = dict_from_csv(roster, 'github_username', 'identifier')
            logger.debug(pformat(id_student_map))
        except Exception as ex:
            logger.error(f"Error encountered while processing roster: {ex}")
            sys.exit(1)


    if assignment_id:
        assignment = get_assignment(assignment_id)
    else:
        classroom: Classroom = choose_classroom()
        assignment: Assignment = choose_assignment(classroom)

    if not assignment:
        logger.fatal("Unable to find the requested assignment.")
        sys.exit(1)
    
    draw_double_line()
    print(assignment)
    draw_single_line()

    clone_submissions(root_dir, assignment, id_student_map, remove_prefix, update, preview)


def clone_submissions(root_dir: Path,
                      assignment: Assignment,
                      id_student_map: Dict[str, str] = None,
                      remove_prefix: bool = False,
                      update: bool = False,
                      preview: bool = False):
    """clone all student submissions for an assignment into root_dir."""

    if id_student_map and assignment.type != 'individual':
        logger.fatal("Use of GitHub classroom roster only valid for individual assignments.")
        sys.exit(1)
    
    with yaspin(text="Retrieving data from GitHub. Please wait...").aesthetic:
        accepted = get_accepted_assignments(assignment)
    submitted = [a for a in accepted if a.commit_count > 0]
    logger.debug(pformat(submitted))

    submitted_repos = {a.repository.name:a.repository for a in submitted}

    repo_dirs: Dict[str, GitRepo] = {}
    other_dirs: List[str] = []
    with yaspin(text="Checking for existing repositories").aesthetic:
        for sub_dir in root_dir.iterdir():
            if not sub_dir.is_dir():
                continue
            try:
                repo_dirs[sub_dir.name] = GitRepo(sub_dir)
            except:
                other_dirs.append(sub_dir)
                continue

    logger.debug("repo_dirs: " + pformat(repo_dirs.keys()))
    logger.debug("other_dirs: " + pformat(other_dirs))

    clone_repos: Dict[str, str] = {}
    pull_repos: List[GitRepo] = []
    bad_repos: List[str] = []
    if not id_student_map:
        # no renaming, so this is easy
        clone_repos = {a.repository.name:a.repository.html_url for a in submitted if a.repository.name not in repo_dirs}
        pull_repos = [repo_dirs.get(a.repository.name) for a in submitted if a.repository.name in repo_dirs]
        bad_repos = [a.repository.name for a in submitted if a.repository.name in other_dirs]
    else:
        # Can assume these are individual assignments so...
        submitted_ids = [a.students[0].login for a in submitted]
        unsubmitted_students = [v for k, v in id_student_map.items() if not k in submitted_ids]
        for name in unsubmitted_students:
            logger.info(f"{name} has not submited the assignment, so not cloning")
        id_repo_url_map = {a.students[0].login:a.repository.html_url for a in submitted}

        # sort the ids largest to smallest to avoid potential issue with 1 id
        # being a substring of another
        submitted_ids.sort(key=lambda s: len(s), reverse=True)

        # map to repos that have already been pulled
        for dir_name in repo_dirs:
            found = None
            for id in submitted_ids:
                if id in dir_name:
                    found = id
                    pull_repos.append(repo_dirs.get(dir_name))
                    break
            if found: submitted_ids.remove(found)
        
        # determine the directory name to use for any new clones
        re_invalid = re.compile(r'([<>:"\/\\\,|?*]|\s)+')
        id_dir_map: Dict[str, str] = {}
        for id in submitted_ids:
            prefix = assignment.slug
            student_name = id_student_map.get(id)
            if student_name:
                student_name = re_invalid.sub('_', student_name)
                student_name = student_name.replace('__', '_')
                dir_name = student_name + "@" + id
            else:
                dir_name = id
            if not remove_prefix:
                dir_name = prefix + '-' + dir_name
            id_dir_map[id] = dir_name

        logger.debug("id_dir_map: " + pformat(id_dir_map))

        # if not pulled, make sure the directory isn't corrupted somehow
        for other_dir in other_dirs:
            for id, dir_name in id_dir_map.items():
                if dir_name == other_dir:
                    found = id
                    bad_repos.append(dir_name)
                    break
            if found: submitted_ids.remove(found)

        # the remaining items in submitted_ids will be the repositories that
        # need to be cloned
        clone_repos = {id_dir_map[id]:id_repo_url_map[id] for id in submitted_ids}

    for bad_repo in bad_repos:
        logger.warning(f"{bad_repo} was expected to be a Git repository, but either it is not or it is corrupted. Skipping.")

    logger.debug("clone_repos: " + pformat(clone_repos))
    logger.debug("pull_repos" + pformat(pull_repos))

    for dir_name, repo_url in clone_repos.items():
        if preview:
            print(f"WOULD CLONE {dir_name} from {repo_url}")
        else:
            logger.info(f"CLONING {dir_name} from {repo_url} ")
            repo_path = root_dir / dir_name
            try:
                GitRepo.clone(repo_url, repo_path)
            except:
                logger.exception(f"Exception raised while cloning from {repo_url} into {repo_path}")

    if update:
        for repo in pull_repos:
            if preview:
                print(f"WOULD PULL {repo.common_dir}")
            else:
                logger.info(f"PULLING from {repo.working_dir}")
                try:
                    repo.pull()
                except:
                    logger.exception(f"Exception raised while cloning from {repo_url} into {repo_path}")

if __name__ == '__main__':
    clone_submissions_cmd()
