from typing import List

import logging
from pathlib import Path
from git import Repo

logger = logging.getLogger(__name__)

def get_git_dirs(base_dir: Path) -> List[Path]:
    if not base_dir.is_dir():
        raise FileNotFoundError(f"{base_dir} is not a directory")

    git_dirs = []

    for sub_path in base_dir.iterdir():
        logger.debug(f'is {sub_path} a Git repo?')
        if sub_path.is_dir():
            # quick and dirty
            # 
            # git_dir = sub_path / '.git'
            # if git_dir.is_dir():
            #     git_dirs.append(sub_path)

            # slower but safer
            # 
            try:
                Repo(sub_path)
                logger.debug(f'YES')
                git_dirs.append(sub_path)
            except:
                logger.debug(f'NO')
                pass
    
    return git_dirs
