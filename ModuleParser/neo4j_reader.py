from py2neo import Graph
import config


def get_graph():
    if config.NEO4J_PWD is not None:
        graph = Graph(uri=config.NEO4J_URI, password=config.NEO4J_PWD)
    else:
        graph = Graph(uri=config.NEO4J_URI)
    return graph


def get_all_pyvers():
    graph = get_graph()
    cypher = "MATCH (v:PythonVersion) " \
             "return v"
    result = graph.run(cypher)
    data = result.data()
    versions = [d['v']['name'].split("#")[-1] for d in data]
    return versions


def get_pyvers_by_module(std_module):
    graph = get_graph()
    cypher = "MATCH (:StandardModule{{name: '{}'}})<-[:HasModule]-(v:PythonVersion) " \
             "RETURN v".format(std_module)
    result = graph.run(cypher)
    data = result.data()
    versions = [d['v']['name'].split("#")[-1] for d in data]
    return versions


def get_pkgvers_by_module(third_module):
    graph = get_graph()
    cypher = "MATCH (:ThirdPartyModule{{name: '{}'}})<-[:HasModule]-(v:PythonPackageVersion) " \
             "RETURN v".format(third_module)
    result = graph.run(cypher)
    data = result.data()
    pkgvers = [d['v']['name'] for d in data]
    return pkgvers


def get_pkgvers_by_module_pyvers(third_module, pyvers):
    graph = get_graph()
    pkgvers = list()
    for pyver in pyvers:
        pyver_name = "python#{}".format(pyver)
        cypher = "MATCH (:ThirdPartyModule{{name: '{}'}})<-[:HasModule]-(v:PythonPackageVersion)" \
                 "-[:CompatibleWith]->(:PythonVersion{{name: '{}'}})" \
                 "RETURN v".format(third_module, pyver_name)
        result = graph.run(cypher)
        data = result.data()
        pkgvers.extend([d['v']['name'] for d in data])
    pkgvers = list(set(pkgvers))
    return pkgvers


def get_pkgvers_by_module_os(third_module, os):
    graph = get_graph()
    cypher = "MATCH (:ThirdPartyModule{{name: '{}'}})<-[:HasModule]-(v:PythonPackageVersion)<-[:HasVersion]-" \
             "(:PythonPackage)-[:CompatibleWith]->(:OperatingSystem{{name: '{}'}}) " \
             "RETURN v".format(third_module, os)
    result = graph.run(cypher)
    data = result.data()
    pkgvers = [d['v']['name'] for d in data]
    return pkgvers


def get_python_features():
    graph = get_graph()
    cypher = "MATCH p=(:PythonFeature)<-[:HasFeature]-(:PythonVersion)" \
             "RETURN p"
    result = graph.run(cypher)
    data = result.data()
    feature_dict = dict()
    for d in data:
        relation = d['p']
        feature_node = relation.start_node
        regex = feature_node['regex']
        pyver_node = relation.end_node
        version = pyver_node['name'].split("#")[-1]
        if regex not in feature_dict:
            feature_dict[regex] = list()
        feature_dict[regex].append(version)
    return feature_dict


def get_os_by_pkg(pkgmth):
    graph = get_graph()
    cypher = "MATCH (:PythonPackage{{name: '{}'}})-[:CompatibleWith]->(v:OperatingSystem)" \
             "RETURN v".format(pkgmth)
    result = graph.run(cypher)
    data = result.data()
    os_list = [d['v']['name'] for d in data]
    return os_list


def get_std_top_modules():
    graph = get_graph()
    cypher = "MATCH p=(v:PythonVersion)-[:HasModule]->(n:StandardModule)" \
             "RETURN p"
    result = graph.run(cypher)
    data = result.data()
    std_dict = dict()
    for d in data:
        relation = d['p']
        start = relation.start_node
        end = relation.end_node
        pyver = start['name'].split("#")[-1]
        if pyver not in std_dict:
            std_dict[pyver] = list()
        module = end['name']
        if "." not in module:
            std_dict[pyver].append(module)

    return std_dict


def get_rank_by_pkg(pkg):
    graph = get_graph()
    cypher = "MATCH (v:PythonPackage{{package: '{}'}})" \
             "RETURN v".format(pkg)
    result = graph.run(cypher)
    data = result.data()
    try:
        d = data[0]
        rank = d['v']['rank']
        if rank is None:
            rank = 0
        return rank
    except (IndexError, KeyError):
        return 0
