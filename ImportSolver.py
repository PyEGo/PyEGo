import os
from ModuleParser.module_parser import parse_pyvers_and_pkgvers
from PackageSolver.package_solver import solve_package
from OutputGenerator.dockerfile_generator import generate_dockerfile
from OutputGenerator.json_generator import generate_json
from utils import write_object_to_file


def get_folder_path(path):
    # parts = path.split(os.sep)[:-1]
    # folder_path = os.sep.join(parts)
    # if folder_path == "":
    #     folder_path = os.sep
    # return folder_path
    return os.path.dirname(path)


def solve_import(root, dst_path=None,
                 add_path=None, extra_run_lines=None, cmd_lines=None,
                 select_pkgs="select-one", optim_target="approximate", explicit_installed="direct",
                 output_type="Dockerfile"):
    while root.endswith(os.sep):
        root = root[:-1]
    pkgver_dict, msg = parse_pyvers_and_pkgvers(root, select_pkgs=select_pkgs)
    if pkgver_dict is None:
        return None
    pkgvers, sys_pkgs, pyver = solve_package(pkgver_dict,
                                             optim_target=optim_target, explicit_installed=explicit_installed)
    if pkgvers is None:
        return None

    if output_type == "Dockerfile":
        if add_path is None:
            add_path = root
        output = generate_dockerfile(pkgvers, sys_pkgs, add_path, msg,
                                         pyver=pyver, extra_run_lines=extra_run_lines, cmd_lines=cmd_lines)
        if not dst_path:
            folder_path = get_folder_path(root)
            dst_path = os.path.join(folder_path, "Dockerfile")
        if not dst_path.endswith("Dockerfile") and os.path.exists(dst_path) and os.path.isdir(dst_path):
            dst_path = os.path.join(dst_path, "Dockerfile")
        dst_file = open(dst_path, "w")
        dst_file.writelines(output)
        dst_file.close()
    else:  # json
        output = generate_json(pkgvers, sys_pkgs, pyver, msg)
        if not dst_path:
            folder_path = get_folder_path(root)
            dst_path = os.path.join(folder_path, "dependency.json")
        if not dst_path.endswith("dependency.json") and os.path.exists(dst_path) and os.path.isdir(dst_path):
            dst_path = os.path.join(dst_path, "dependency.json")
        write_object_to_file(dst_path, output)
    return dst_path, msg

