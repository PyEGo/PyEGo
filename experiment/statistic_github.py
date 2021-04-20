import os
import ast
from utils import read_object_from_file


class Project:
    def __init__(self, root):

        def extract_all_py_filepath(root):
            py_files = list()
            for curr_dir, folders, files in os.walk(root):
                for file in files:
                    if not file.endswith(".py"):
                        continue
                    path = os.path.join(curr_dir, file)
                    py_files.append(path)
            return py_files

        self.root = root
        if os.path.isdir(root):
            self.files = extract_all_py_filepath(root)
        else:
            self.files = ["--", ]

    def count_files(self):
        return len(self.files)

    def count_loc(self):
        loc = 0
        for file in self.files:
            if file == "--":
                path = self.root
            else:
                path = os.path.join(self.root, file)
            with open(path) as f:
                lines = f.readlines()
                loc += len(lines)
        return loc

    def count_import(self):
        def has_body(node):
            types = [ast.ClassDef, ast.FunctionDef, ast.If, ast.For, ast.While]
            for tp in types:
                if isinstance(node, tp):
                    return True
            return False

        def parse_body(body, count):
            for node in body:
                if isinstance(node, ast.Import):
                    count += 1
                if isinstance(node, ast.ImportFrom):
                    count += 1
                if has_body(node):
                    node_body = node.body
                    count = parse_body(node_body, count)
                    if isinstance(node, ast.If):
                        node_body = node.orelse
                        count = parse_body(node_body, count)
            return count

        import_lines = 0
        for file in self.files:
            if file == "--":
                path = self.root
            else:
                path = os.path.join(self.root, file)
            with open(path) as f:
                lines = f.readlines()
            try:
                root_node = ast.parse("".join(lines))
            except SyntaxError:
                continue
            import_lines = parse_body(root_node.body, import_lines)
        return import_lines


def statistic_one(root):
    project = Project(root)
    files = project.count_files()
    loc = project.count_loc()
    import_lines = project.count_import()
    return files, loc, import_lines


def statistic_all(root, metadata):
    tot_files, tot_loc, tot_import_lines = 0, 0, 0
    max_files, max_loc, max_import_lines = 0, 0, 0
    min_files, min_loc, min_import_lines = 999999, 999999, 999999
    count = len(metadata)
    for project in metadata:
        code_root = project["coderoot"]
        path = os.path.join(root, code_root)
        files, loc, import_lines = statistic_one(path)

        tot_files += files
        tot_loc += loc
        tot_import_lines += import_lines
        max_files = max(max_files, files)
        max_loc = max(max_loc, loc)
        max_import_lines = max(max_import_lines, import_lines)
        min_files = min(min_files, files)
        min_loc = min(min_loc, loc)
        min_import_lines = min(min_import_lines, import_lines)
    avg_files = 1.*tot_files/count
    avg_loc = 1.*tot_loc/count
    avg_import_lines = 1.*tot_import_lines/count
    print("AVG:")
    print("files:{}, loc:{}, imports:{}".format(avg_files, avg_loc, avg_import_lines))
    print("MAX:")
    print("files:{}, loc:{}, imports:{}".format(max_files, max_loc, max_import_lines))
    print("MIN:")
    print("files:{}, loc:{}, imports:{}".format(min_files, min_loc, min_import_lines))

