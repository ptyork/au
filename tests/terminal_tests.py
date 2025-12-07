# Interactive tests only
if __name__ == "__main__":

    from au.common import select_file, select_choice, select_dir

    path = select_file(glob="*.py", title="CHOOSE ROSTER")
    print(str(path))

    path = select_dir(title="CHOOSE DIR")
    print(str(path))

    path = select_dir(title="CHOOSE DIR", exclude_dunder=False, exclude_hidden=False)
    print(str(path))

    choices = [f"Choice #{num}" for num in range(1, 11)]
    sel = select_choice(choices, "PICK ONE OF THESE")
    print(sel if sel is None else f"{sel} {choices[sel]}")
