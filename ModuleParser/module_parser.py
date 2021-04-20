import os
import re

import config
from ModuleParser.file_parser import parse_import_modules
from ModuleParser.folder_parser import extract_all_py_filepath, parse_custom_top_levels
from ModuleParser.module_filter import filter_custom_modules, apart_standard_modules
from utils import read_object_from_file, write_object_to_file
from ModuleParser.neo4j_reader import get_pyvers_by_module, get_all_pyvers, \
    get_python_features, get_pkgvers_by_module_pyvers, get_os_by_pkg, get_std_top_modules, get_rank_by_pkg

std_top_levels = read_object_from_file(config.STD_TOP_CACHE_PATH)
if not std_top_levels:
    std_top_levels = get_std_top_modules()
    write_object_to_file(config.STD_TOP_CACHE_PATH, std_top_levels)


def parse_modules(root):
    # both file and folder are ok
    # extract all custom top level modules and python files
    custom_top_levels = list()
    all_py_filepath = list()
    if os.path.isdir(root):
        custom_top_levels.extend(parse_custom_top_levels(root, need_init=False))
        all_py_filepath.extend(extract_all_py_filepath(root))
    elif root.endswith(".py"):
        all_py_filepath.append(root)
    else:
        return None, None, None, None

    # extract top and second level modules used
    top_levels = list()
    second_levels = list()
    for file in all_py_filepath:
        with open(file) as f:
            lines = f.readlines()
            code = "".join(lines)
            top_level, second_level = parse_import_modules(code)
            top_levels.extend(top_level)
            second_levels.extend(second_level)

    # filter custom modules, apart 3rd and std modules
    top_levels = list(set(top_levels))
    second_levels = list(set(second_levels))
    std_3rd_tops, std_3rd_seconds = filter_custom_modules(top_levels, second_levels, custom_top_levels)

    std_top_levels_list = list()
    for pyver in std_top_levels:
        std_top_levels_list.extend(std_top_levels[pyver])
    std_top_levels_list = list(set(std_top_levels_list))
    std_tops, std_seconds, third_tops, third_seconds = apart_standard_modules(std_3rd_tops,
                                                                              std_3rd_seconds, std_top_levels_list)
    return std_tops, std_seconds, third_tops, third_seconds


def get_all_pkgvers(modules, pyvers):
    # modules: list(), pyvers: list(), graph: py2neo.Graph
    # return: dict():{module1: [pkg1#ver1#mth1, pkg2#ver2#mth2], }
    module_dict = dict()
    for module in modules:
        curr_pkgver_list = get_pkgvers_by_module_pyvers(module, pyvers)
        if len(curr_pkgver_list) == 0:
            continue
        module_dict[module] = curr_pkgver_list
    return module_dict


def filter_pkgvers_by_os(module_dict):
    # module_dict: dict():{module1: [pkg1#ver1#mth1, pkg2#ver2#mth2], }
    # return: filtered_dict: dict():{module1: [pkg1#ver1#mth1, pkg2#ver2#mth2], }
    # return: msg: str, incompatible msg
    msg = None
    filtered_dict = dict()
    incompatible_os = set()
    for module in module_dict:
        pkgver_list = module_dict[module]
        filtered_dict[module] = list()
        for pkgver in pkgver_list:
            pkg, ver, mth = pkgver.split("#")
            pkgmth = "{}#{}".format(pkg, mth)
            os_list = get_os_by_pkg(pkgmth)
            if "linux" not in os_list:
                incompatible_os = incompatible_os.union(set(os_list))
            else:
                filtered_dict[module].append(pkgver)
            if msg is None and len(filtered_dict[module]) == 0:
                msg = "It seems like module {} (package {}) is only compatible with {}".format(module, pkg, incompatible_os)
    return filtered_dict, msg


def filter_pkgvers_by_rank(module_dict):
    filtered_dict = dict()
    for module in module_dict:
        pkgver_list = module_dict[module]
        filtered_dict[module] = list()
        pkgs = [pkgver.split("#")[0] for pkgver in pkgver_list]
        pkgs = list(set(pkgs))
        highest_rank_pkgs = get_highest_rank_pkg(pkgs)
        for pkgver in pkgver_list:
            pkg = pkgver.split("#")[0]
            if pkg not in highest_rank_pkgs:
                continue
            filtered_dict[module].append(pkgver)
    return filtered_dict


def get_highest_rank_pkg(pkgs):
    max_rank = -1
    target = ""
    apts = list()  # preserve both python-xx and python3-xx
    for pkg in pkgs:
        rank = get_rank_by_pkg(pkg)
        if rank > max_rank:
            target = pkg
            max_rank = rank
        if rank == 0:
            apts.append(pkg)
    targets = apts
    targets.append(target)
    return list(set(targets))


def parse_first_method(module_dict):
    # module_dict: dict():{module1: [pkg1#ver1#mth1, pkg2#ver2#mth2], }
    # return: "pip" or "apt"
    first_method = "pip"  # pip first default
    for module in module_dict:
        pkgver_list = module_dict[module]
        methods = [pkgver.split("#")[-1] for pkgver in pkgver_list]
        if "pip" not in methods:
            first_method = "apt"  # use apt once, try to use apt everywhere
            return first_method
    return first_method


def filter_unused_pkgs(module_dict, first_method):
    # module_dict: dict():{module1: [pkg1#ver1#mth1, pkg2#ver2#mth2], }
    # return: filtered_dict: dict():{module1: [pkg1#ver1#mth1, pkg2#ver2#mth2], }
    filtered_dict = dict()
    for module in module_dict:
        pkgver_list = module_dict[module]
        filtered_dict[module] = pkgver_list
        methods = [pkgver.split("#")[-1] for pkgver in pkgver_list]
        if first_method not in methods:
            continue
        else:
            filtered = [pkgver for pkgver in pkgver_list if pkgver.split("#")[-1] == first_method]
            filtered_dict[module] = filtered
    return filtered_dict


def convert_to_pkgver_dict(module_dict):
    # module_dict: dict():{module1: [pkg1#ver1#mth1, pkg2#ver2#mth2], }
    # return: dict():{pkg1#mth1: [ver1, ver2], pkg2#mth2: [ver1, ver2]}
    pkgver_dict = dict()
    for module in module_dict:
        tmp_dict = dict() 
        pkgver_list = module_dict[module]
        for pkgver in pkgver_list:
            pkg, ver, mth = pkgver.split("#")
            pkgmth = "{}#{}".format(pkg, mth)
            if pkgmth not in tmp_dict:
                tmp_dict[pkgmth] = set()
            tmp_dict[pkgmth].add(ver)

        for pkgmth in tmp_dict:
            if pkgmth not in pkgver_dict:
                pkgver_dict[pkgmth] = tmp_dict[pkgmth]
            else:
                pkgver_dict[pkgmth] = pkgver_dict[pkgmth].intersection(tmp_dict[pkgmth])
    return pkgver_dict


def get_pkgvers(third_tops, third_seconds, pyvers, select_pkgs="select-one"):
    # get PackageVersions contain 3rd party modules
    modules = third_tops
    modules.extend(third_seconds)

    module_dict = get_all_pkgvers(modules, pyvers)
    filtered_dict, msg = filter_pkgvers_by_os(module_dict)
    if msg is not None:
        print(msg)
    first_method = parse_first_method(module_dict)

    filtered_dict = filter_unused_pkgs(filtered_dict, first_method)
    if select_pkgs == "select-one":
        filtered_dict = filter_pkgvers_by_rank(filtered_dict)
    if select_pkgs == "select-all":
        pass
    pkgvers = convert_to_pkgver_dict(filtered_dict)
    return pkgvers, msg


def get_pyvers_by_modules(std_tops, std_seconds):
    # get PythonVersions contain standard modules
    pyvers = set(get_all_pyvers())
    modules = std_tops
    modules.extend(std_seconds)
    for module in modules:
        curr_vers = set(get_pyvers_by_module(module))
        if len(curr_vers) == 0:
            continue  # unrecorded second level module
        pyvers = pyvers.intersection(curr_vers)
    return pyvers


def get_pyvers_by_features(root):
    feature_dict = get_python_features()
    pyvers = set(get_all_pyvers())
    all_py_filepath = list()
    if os.path.isdir(root):
        all_py_filepath.extend(extract_all_py_filepath(root))
    elif root.endswith(".py"):
        all_py_filepath.append(root)
    for regex in feature_dict:
        curr_pyvers = feature_dict[regex]
        pattern = re.compile(regex)
        matched = False
        for path in all_py_filepath:
            with open(path) as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("#"):
                        continue
                    if pattern.match(line):
                        # print(regex)
                        # print(line)
                        matched = True
                        break
            if matched:
                pyvers = pyvers.intersection(curr_pyvers)
                break
    return pyvers


def get_pyvers(root, std_tops, std_seconds):
    vers1 = get_pyvers_by_modules(std_tops, std_seconds)
    vers2 = get_pyvers_by_features(root)
    pyvers = vers1.intersection(vers2)
    if len(pyvers) == 0:
        pyvers = vers1  # trick
    # if len(pyvers) != 1 and "3.9" in pyvers:
    #     pyvers.remove("3.9")  # have a try!
    return pyvers


def filter_bad_pkgs(pkgver_dict):
    # follow pkgs are:
    # 1. has superordinate substitution
    # 2. has strict Python version & OS & architecture specification, and METADATA is erroneous
    # these pkgs are summarized by pratice, we can just use superordinate substitution instead of them
    bad_pkgs = ["scipy-mpmkp#pip", "pandas-mpmkp#pip", "numpy-mkp2020#pip", "numpy-mips64#pip",
                "requestsaa#pip", "dlorenc-requests#pip", "degree72-requests#pip", "pillow-simd#pip",
                "mysql-python#pip", "dnslib#pip", "distribute#pip"]
    for bad in bad_pkgs:
        if bad in pkgver_dict:
            pkgver_dict.pop(bad)
    return pkgver_dict


def parse_pyvers_and_pkgvers(root, select_pkgs="select-one"):
    std_tops, std_seconds, third_tops, third_seconds = parse_modules(root)
    if std_tops is None:
        return None, None
    pyvers = get_pyvers(root, std_tops, std_seconds)
    if len(pyvers) == 0:
        return None, None
    pkgvers, msg = get_pkgvers(third_tops, third_seconds, pyvers, select_pkgs=select_pkgs)
    if select_pkgs == "select-all":
        pkgvers = filter_bad_pkgs(pkgvers)  # filter some packages which usually lead to build failed
    pkgvers["python#apt"] = pyvers
    return pkgvers, msg



