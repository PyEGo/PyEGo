import os


def extract_all_py_filepath(root):
    py_files = list()
    for curr_dir, folders, files in os.walk(root):
        for file in files:
            if not file.endswith(".py"):
                continue
            path = os.path.join(curr_dir, file)
            py_files.append(path)
    return py_files


def parse_modules_by_dir_content(pkg_dir, need_init=True):
    modules = list()
    filenames = os.listdir(pkg_dir)
    for filename in filenames:
        fullpath = os.path.join(pkg_dir, filename)
        if os.path.isdir(fullpath):
            subs = os.listdir(fullpath)
            if need_init and "__init__.py" not in subs:
                continue
            modules.append(filename)  # folder is a module
        elif filename.endswith(".py") or filename.endswith(".so"):
            if filename == "setup.py" or filename.startswith("__"):
                continue
            modules.append(filename.split(".")[0])  # py file or so file is a module

    return modules


def parse_custom_top_levels(root, need_init=True):
    top_levels = parse_modules_by_dir_content(root, need_init)
    return top_levels


def parse_custom_second_levels(root, top_levels):
    files = os.listdir(root)
    second_levels = list()
    for top in top_levels:
        if top not in files:
            continue  # only parse folder top level
        path = os.path.join(root, top)
        if not os.path.isdir(path):
            continue
        modules = parse_modules_by_dir_content(path)
        modules = ["{}.{}".format(top, sub) for sub in modules]
        second_levels.extend(modules)
    return second_levels


