from typed_ast import ast27
import ast


def has_body(node):
    types = [ast.ClassDef, ast.FunctionDef, ast.If, ast.For, ast.While, ast.Try,
             ast27.ClassDef, ast27.FunctionDef, ast27.If, ast27.For, ast27.While, ast27.TryExcept]
    for tp in types:
        if isinstance(node, tp):
            return True
    return False


def parse_body(body, modules, import_func, importfrom_func):
    for node in body:
        if isinstance(node, ast27.Import) or isinstance(node, ast.Import):
            modules.extend(import_func(node))
        if isinstance(node, ast27.ImportFrom) or isinstance(node, ast.ImportFrom):
            modules.extend(importfrom_func(node))
        if has_body(node):
            node_body = node.body
            modules = parse_body(node_body, modules, import_func, importfrom_func)
            if isinstance(node, ast.If) or isinstance(node, ast27.If):
                node_body = node.orelse
                modules = parse_body(node_body, modules, import_func, importfrom_func)
    return modules


def parse_top_level_ast(code):
    top_levels = list()
    try:
        root_node = ast.parse(code)
    except SyntaxError:
        try:
            root_node = ast27.parse(code)
            # root_node = py2to3(root_node)
        except SyntaxError:
            return list()

    # for node in root_node.body:
    #     if isinstance(node, ast27.Import) or isinstance(node, ast.Import):
    #         top_levels.extend(parse_import_node_top_levels(node))
    #     if isinstance(node, ast27.ImportFrom) or isinstance(node, ast.ImportFrom):
    #         top_levels.extend(parse_importfrom_node_top_level(node))
    # top_levels = list(set(top_levels))
    top_levels = parse_body(root_node.body, top_levels,
                            parse_import_node_top_levels,
                            parse_importfrom_node_top_levels)
    return top_levels


def parse_import_node_top_levels(node):
    top_levels = list()
    stmts = node.names
    for stmt in stmts:
        top_levels.append(stmt.name.split('.')[0])
    return top_levels


def parse_importfrom_node_top_levels(node):
    module = node.module
    if node.level != 0:
        return list()  # relative import
    if module:
        top_level = module.split('.')[0]
        return [top_level, ]
    else:
        return list()


def parse_second_level_ast(code):
    second_levels = list()
    try:
        root_node = ast.parse(code)
    except SyntaxError:
        try:
            root_node = ast27.parse(code)
        except (SyntaxError, RuntimeError):
            return list()

    # for node in root_node.body:
    #     if isinstance(node, ast27.Import) or isinstance(node, ast.Import):
    #         second_levels.extend(parse_import_node_second_levels(node))
    #     if isinstance(node, ast27.ImportFrom) or isinstance(node, ast.ImportFrom):
    #         second_levels.extend(parse_importfrom_node_second_levels(node))
    # second_levels = list(set(second_levels))
    second_levels = parse_body(root_node.body, second_levels,
                               parse_import_node_second_levels,
                               parse_importfrom_node_second_levels)
    return second_levels


def parse_import_node_second_levels(node):
    second_levels = list()
    stmts = node.names
    for stmt in stmts:
        parts = stmt.name.split('.')
        if len(parts) < 2:
            continue
        second_level = "{}.{}".format(parts[0], parts[1])
        second_levels.append(second_level)
    return second_levels


def parse_importfrom_node_second_levels(node):
    second_levels = list()
    if node.level != 0:
        return list()  # relative import
    module = node.module
    stmts = ["{}.{}".format(module, n.name) for n in node.names]
    for stmt in stmts:
        parts = stmt.split('.')
        if len(parts) < 2:
            continue
        second_level = "{}.{}".format(parts[0], parts[1])
        second_levels.append(second_level)
    return second_levels


def parse_import_modules(code):
    top_levels = parse_top_level_ast(code)
    second_levels = parse_second_level_ast(code)
    return top_levels, second_levels




