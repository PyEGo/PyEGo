from py2neo import Graph
from queue import Queue
import config
from utils import read_object_from_file, write_object_to_file


def get_graph():
    if config.NEO4J_PWD is not None:
        graph = Graph(uri=config.NEO4J_URI, password=config.NEO4J_PWD)
    else:
        graph = Graph(uri=config.NEO4J_URI)
    return graph


def get_pkgvers_by_pkg(pkg):
    graph = get_graph()
    cypher = "MATCH (:PythonPackage{{name: '{}'}})-[:HasVersion]-(node:PythonPackageVersion)" \
             "RETURN node".format(pkg)
    result = graph.run(cypher)
    data = result.data()
    versions = [d['node']['version'] for d in data]
    return versions


def get_dep_py_pkgs(pkgver):
    graph = get_graph()
    cypher = "MATCH (:PythonPackageVersion{{name: '{}'}})-[:DependsOn*1..2]->(:PythonPackageVersion)" \
             "<-[:HasVersion]-(node:PythonPackage)" \
             "RETURN node".format(pkgver)
    result = graph.run(cypher)
    data = result.data()
    pkgs = [d['node']['package'] for d in data]
    return pkgs


def get_pyvers_by_pkgver(pkgver):
    graph = get_graph()
    cypher = "MATCH (:PythonPackageVersion{{name: '{}'}})-[:CompatibleWith]-(v:PythonVersion) " \
             "RETURN v".format(pkgver)
    result = graph.run(cypher)
    data = result.data()
    versions = [d['v']['name'] for d in data]
    return versions


def get_dep_sys_pkgs(pkgver):
    graph = get_graph()
    cypher = "MATCH (:PythonPackageVersion{{name: '{}'}})-[:DependsOn]->(node:SystemPackageVersion) " \
             "RETURN node".format(pkgver)
    result = graph.run(cypher)
    data = result.data()
    pkgvers = [d['node']['name'] for d in data]
    return pkgvers


def get_pip_deps():
    graph = get_graph()
    cypher = "MATCH p=(:PythonPackageVersion)-[:DependsOn]->(:PythonPackageVersion) " \
             "RETURN p"
    result = graph.run(cypher)
    data = result.data()
    deps_dict = dict()
    for d in data:
        relation = d['p']
        start = relation.start_node
        end = relation.end_node
        pkg1, ver1, _ = start['name'].split("#")
        pkg2, ver2, _ = end['name'].split("#")
        if pkg1 not in deps_dict:
            deps_dict[pkg1] = dict()
        if ver1 not in deps_dict[pkg1]:
            deps_dict[pkg1][ver1] = list()
        pkgver2 = "{}#{}".format(pkg2, ver2)
        deps_dict[pkg1][ver1].append(pkgver2)

    return deps_dict


def query(pkg, ver):
    graph = get_graph()
    cypher = f"MATCH (:PythonPackageVersion{{package: '{pkg}', version: '{ver}'}})-[:DependsOn]->(n:PythonPackageVersion) " \
             "RETURN n"
    result = graph.run(cypher)
    data = result.data()
    related = list()
    for d in data:
        node = d['n']
        related.append(f"{node['package']}#{node['version']}")
    return related


def get_related_pkg_dict_no_cache(pkgvers):
    pkg_dict = dict()
    # init
    queue = Queue()
    for pkgmth in pkgvers:
        pkg, method = pkgmth.split("#")
        if method == "apt":
            continue
        vers = pkgvers[pkgmth]
        for ver in vers:
            pkgver = "{}#{}".format(pkg, ver)
            queue.put(pkgver)

    while queue.qsize() > 0:
        pkgver = queue.get()
        pkg, ver = pkgver.split("#")[:2]
        if pkg == "python":
            continue

        if pkg not in pkg_dict:
            pkg_dict[pkg] = dict()
        if ver in pkg_dict[pkg]:
            continue

        pkg_dict[pkg][ver] = list()
        try:
            related = query(pkg, ver)
        except KeyError:
            continue

        for dep_pkgver in related:
            pkg_dict[pkg][ver].append(dep_pkgver)
            queue.put(dep_pkgver)

    return pkg_dict


def get_related_pkg_dict(pkgvers):
    pkg_dict = dict()
    # init
    queue = Queue()
    for pkgmth in pkgvers:
        pkg, method = pkgmth.split("#")
        if method == "apt":
            continue
        vers = pkgvers[pkgmth]
        for ver in vers:
            pkgver = "{}#{}".format(pkg, ver)
            queue.put(pkgver)

    # bfs
    while queue.qsize() > 0:
        pkgver = queue.get()
        pkg, ver = pkgver.split("#")[:2]
        if pkg == "python":
            continue

        if pkg not in pkg_dict:
            pkg_dict[pkg] = dict()
        if ver in pkg_dict[pkg]:
            continue

        pkg_dict[pkg][ver] = list()
        try:
            related = pip_deps_dict[pkg][ver]
        except KeyError:
            continue

        for dep_pkgver in related:
            dep_pkg, dep_ver = dep_pkgver.split("#")
            pkg_dict[pkg][ver].append(dep_pkgver)
            queue.put(dep_pkgver)

    return pkg_dict


def add_pyver_deps(dep_dict):
    for pkg in dep_dict:
        ver_dict = dep_dict[pkg]
        for ver in ver_dict:
            pkgver = "{}#{}#pip".format(pkg, ver)
            pyvers = get_pyvers_by_pkgver(pkgver)
            ver_dict[ver].extend(pyvers)
    # python version
    dep_dict["python"] = dict()
    for ver in config.PY_VERSIONS:
        dep_dict["python"][ver] = list()

    return dep_dict


def add_apt_pkgs(dep_dict, pkgver_dict):
    for pkgmth in pkgver_dict:
        pkg, method = pkgmth.split("#")
        if method == "pip" or pkg == "python":
            continue
        dep_dict[pkgmth] = dict()
        ver_dict = pkgver_dict[pkgmth]
        for ver in ver_dict:
            dep_dict[pkgmth][ver] = list()
    return dep_dict


def convert_pkgvers_to_constrain_dict(pkgvers):
    constrain_dict = dict()
    for pkgmth in pkgvers:
        pkg, method = pkgmth.split("#")
        if method == "pip" or pkg == "python":
            constrain_dict[pkg] = pkgvers[pkgmth]
        else:
            constrain_dict[pkgmth] = pkgvers[pkgmth]
    return constrain_dict


pip_deps_dict = read_object_from_file(config.PIP_DEPS_CACHE_PATH)
if not pip_deps_dict:
    print("Caching pip dependencies in file...")
    pip_deps_dict = get_pip_deps()
    write_object_to_file(config.PIP_DEPS_CACHE_PATH, pip_deps_dict)
    print("Dependencies cached.")



