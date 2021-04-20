from functools import cmp_to_key
from z3 import Int, And, Or, simplify, Optimize, Real, ToReal, If
from PackageSolver.neo4j_reader import get_related_pkg_dict, convert_pkgvers_to_constrain_dict,\
    add_pyver_deps, add_apt_pkgs, pip_deps_dict, get_dep_sys_pkgs
from utils import compare_version
from ModuleParser.module_parser import parse_pyvers_and_pkgvers


def build_int_dict(pkg_dict):
    # arrange a Int z3 variable for each package and stores in a dict
    int_dict = dict()
    for pkg in pkg_dict:
        int_dict[pkg] = Int(pkg)
    return int_dict


def build_order_dict(pkg_dict):
    # arrange a int value for each package version and stores mapping relations in a dict
    # versions are indexed from earliest to latest
    # A has version 1.3, 1.5, 1.8 -> "A": {"1.3": 1, "1.5":2, "1.8":3}
    order_dict = dict()
    for pkg in pkg_dict:
        ver_dict = pkg_dict[pkg]
        order_dict[pkg] = dict()
        ind = 0
        versions = list(ver_dict.keys())
        sorted_versions = sorted(versions, key=cmp_to_key(compare_version))
        for ver in sorted_versions:
            order_dict[pkg][ver] = ind
            ind += 1
    return order_dict


def add_dependency_constrains(solver, pkg_dict, order_dict, int_dict):
    # add constrains from package dependencies
    for pkg in pkg_dict:
        ver_dict = pkg_dict[pkg]
        ands = list()
        for ver in ver_dict:
            ind = order_dict[pkg][ver]
            deps = sorted(ver_dict[ver])
            ors = list()
            curr_pkg = None
            or_expr = None
            for dep in deps:
                # convert one pkg dependencies to z3 expr
                # A==1 requires B==2,B==3 -> (B==2 OR B==3)
                dep_pkg, dep_ver = dep.split("#")
                dep_ind = order_dict[dep_pkg][dep_ver]
                if dep_pkg != curr_pkg:
                    if or_expr is not None:
                        ors.append(or_expr)
                    curr_pkg = dep_pkg
                    or_expr = Or()
                expr = Or(int_dict[dep_pkg] == dep_ind)
                or_expr = Or(or_expr, expr)
                or_expr = simplify(or_expr)
            if or_expr is not None:
                ors.append(or_expr)

            # merge all pkg dependencies OR expr for the pkg version
            # A==1 requires B==2,B==3,C==1 -> A==1 AND (B==2 OR B==3) AND C==1
            and_expr = And(int_dict[pkg] == ind)
            for expr in ors:
                and_expr = And(and_expr, expr)
                and_expr = simplify(and_expr)
            ands.append(and_expr)

        # merge all versions dependencies AND expr
        # A==1 requires B==2,B==3,C==1; A==3 requires B==3, C==3
        # -> (A==1 AND (B==2 OR B==3) AND C==1) Or (A==3 AND B==3 AND C==3)
        constrain = Or()
        for expr in ands:
            constrain = Or(constrain, expr)
            constrain = simplify(constrain)
        # situation that the package is unnecessary
        unnecessary_ind = len(order_dict[pkg].keys())
        constrain = Or(constrain, int_dict[pkg] == unnecessary_ind)
        constrain = simplify(constrain)

        # print(constrain)
        solver.add(constrain)
    return solver


def add_int_constrains(solver, pkg_dict, int_dict):
    # add constrains of the number of versions
    # a package's variable should >=0 and < len(versions)
    # and we also consider the situation that the package is unnecessary
    # arrange this situation var = len(versions)
    # so a package's variable should >=0 and <= len(versions)
    for pkg in pkg_dict:
        ver_dict = pkg_dict[pkg]
        ver_len = len(ver_dict.keys())
        constrain = And(int_dict[pkg] >= 0, int_dict[pkg] <= ver_len)
        # print(constrain)
        solver.add(constrain)
    return solver


def add_version_constrains(solver, constrain_version_dict, order_dict, int_dict):
    # add version constrains extracted from module info/ python feature info
    for pkg in constrain_version_dict:
        versions = constrain_version_dict[pkg]
        constrain = Or()
        for ver in versions:
            ind = order_dict[pkg][ver]
            constrain = Or(constrain, int_dict[pkg] == ind)
            constrain = simplify(constrain)

        # print(constrain)
        solver.add(constrain)
    return solver


def add_optimize_targets(solver, int_dict):
    # optimize target1: install least packages
    # optimize target2: install latest version of packages
    # ->maximize(version)
    for pkg in int_dict:
        var = int_dict[pkg]
        solver.maximize(var)
    return solver


def add_optimize_targets2(solver, int_dict, order_dict):
    # new optimize target
    # A*o1+(1-A)*o2
    # o1 = AVG[v'(pkg)/|V(pkg)|] if v'(pkg)!=|V(pkg)| ((not installed))
    # o2 = (|P|-|P'|)/|P| if p is installed, p belongs to P'
    A = 0.5
    o1 = Real("o1")
    o2 = Real("o2")
    sum_ins = Int("sum_ins")
    sum_all = Int("sum_all")
    count_ins = Int("count_ins")
    sum_ins, sum_all, count_ins = 0, 0, 0

    count_all = 0
    for pkg in int_dict:
        sum_ins = If(int_dict[pkg] != len(order_dict[pkg]), sum_ins + int_dict[pkg], sum_ins)
        count_ins = If(int_dict[pkg] != len(order_dict[pkg]), count_ins + 1, count_ins)
        sum_all = If(int_dict[pkg] != len(order_dict[pkg]), sum_all + len(order_dict[pkg]), sum_all)
        count_all += 1

    o1 = ToReal(sum_ins)/ToReal(sum_all)
    o2 = 1-(ToReal(count_ins)/count_all)
    target = A*o1 + (1-A)*o2
    solver.maximize(target)
    return solver


def parse_z3_model(model, int_dict, order_dict):
    pkgvers = dict()
    for pkg in int_dict:
        var = int_dict[pkg]
        ver_ind = model[var]
        vers = [k for k, v in order_dict[pkg].items() if v == ver_ind]
        if len(vers) == 0:
            continue  # ind = len(ver), unnecessary to install
        else:
            ver = vers[0]
            if ver_ind == len(order_dict[pkg])-1:
                latest = True
            else:
                latest = False
        pkgvers[pkg] = (ver, latest)
    return pkgvers


def solve_pkgver_z3(pkg_dict, constrain_version_dict, optim_target="approximate"):
    # solver = Solver()
    solver = Optimize()
    int_dict = build_int_dict(pkg_dict)
    order_dict = build_order_dict(pkg_dict)
    solver = add_dependency_constrains(solver, pkg_dict, order_dict, int_dict)
    solver = add_int_constrains(solver, pkg_dict, int_dict)
    solver = add_version_constrains(solver, constrain_version_dict, order_dict, int_dict)
    if optim_target == "approximate":
        solver = add_optimize_targets(solver, int_dict)
    if optim_target == "exact":
        solver = add_optimize_targets2(solver, int_dict, order_dict)
        solver.set(timeout=60000)
    try:
        if solver.check():
            pkgvers = parse_z3_model(solver.model(), int_dict, order_dict)
            return pkgvers
        else:
            return None
    except:
        return None


def sort_pkgver(pkgver_dict):
    # preprocess
    pkgver_sorted = list()
    apts = [pkg for pkg in pkgver_dict if len(pkg.split("#")) == 2]
    for pkg in apts:
        ver = pkgver_dict.pop(pkg)
        pkgver_sorted.append("{}#{}".format(pkg, ver[0]))

    # init
    sub_dict = dict()
    for pkg, ver in pkgver_dict.items():
        key = "{}#{}".format(pkg, ver[0])
        sub_dict[key] = set()
    pkgver_set = sub_dict.keys()

    # get sub graph
    for pkgver in sub_dict:
        pkg, ver = pkgver.split("#")
        try:
            deps = set(pip_deps_dict[pkg][ver])
        except KeyError:
            deps = set()
        ins = deps.intersection(pkgver_set)
        sub_dict[pkgver] = ins

    # topology sort
    while len(sub_dict) > 0:
        pops = [pkgver for pkgver in sub_dict if len(sub_dict[pkgver]) == 0]
        for pkgver in pops:
            pkgver_sorted.append(pkgver)
            sub_dict.pop(pkgver)
            for key in sub_dict:
                deps = sub_dict[key]
                if pkgver not in deps:
                    continue
                deps.remove(pkgver)
        if len(pops) != 0:
            continue
        for pkgver in sub_dict:
            pkgver_sorted.append(pkgver)
        sub_dict = list()

    return pkgver_sorted


def determine_explict_installation(pkgver_dict, pkgver_sorted, c_dict, explicit_installed="direct"):
    condition = False
    for pkg in pkgver_dict:
        ver, latest = pkgver_dict[pkg]
        if explicit_installed == "direct":
            condition = pkg in c_dict
        if explicit_installed == "direct-and-not-latest":
            condition = pkg in c_dict or not latest

        if condition:
            continue
        pkgver = "{}#{}".format(pkg, ver)
        pkgver_sorted.remove(pkgver)
    return pkgver_sorted


def get_sys_deps(pkgver_dict):
    sys_pkgvers = list()
    for pkg in pkgver_dict:
        ver = pkgver_dict[pkg][0]
        pkgver = "{}#{}#pip".format(pkg, ver)
        sys_pkgvers.extend(get_dep_sys_pkgs(pkgver))
    sys_pkgvers = list(set(sys_pkgvers))
    return sys_pkgvers


def format_py_pkgvers(py_pkgvers, pyver):
    formatted = list()
    for pkgver in py_pkgvers:
        parts = pkgver.split("#")
        if len(parts) == 2:
            # pip package, append "#pip"
            new_pkgver = "{}#pip".format(pkgver)
            formatted.append(new_pkgver)
        if len(parts) == 3:
            # apt package, remove conflict version,reorder
            pkg, method, ver = parts[:3]
            if pyver == "2.7" and "python-" in pkgver:
                new_pkgver = "{}#{}#{}".format(pkg, ver, method)
                formatted.append(new_pkgver)
            if pyver != "2.7" and "python3-" in pkgver:
                new_pkgver = "{}#{}#{}".format(pkg, ver, method)
                formatted.append(new_pkgver)
    return formatted


def solve_package(pkgver_dict, optim_target="approximate", explicit_installed="direct"):
    c_dict = convert_pkgvers_to_constrain_dict(pkgver_dict)
    p_dict = get_related_pkg_dict(pkgver_dict)
    p_dict = add_pyver_deps(p_dict)
    p_dict = add_apt_pkgs(p_dict, pkgver_dict)
    res = solve_pkgver_z3(p_dict, c_dict, optim_target=optim_target)
    if res is None:
        return None, None, None
    if "python" not in res:
        return None, None, None
    pyver = res.pop("python")[0]
    sort = sort_pkgver(res)
    py_pkgvers = determine_explict_installation(res, sort, c_dict, explicit_installed=explicit_installed)
    py_pkgvers = format_py_pkgvers(py_pkgvers, pyver)
    sys_pkgvers = sorted(get_sys_deps(res))
    return py_pkgvers, sys_pkgvers, pyver





