import os


class TestResults:
    def __init__(self, log_name, log_type, dataset="github", logs=None, log_path=None):
        if log_path:
            f = open(log_path)
            logs = f.readlines()
            f.close()
        self.name = log_name
        if log_type == "PyEGo":
            self.results = self.parse_ego_log(logs, dataset)
        else:
            self.results = self.parse_dockerizeme_log(logs)

    def parse_ego_log(self, logs, dataset):
        id = 0
        results = dict()
        for log in logs:
            log = log.strip()
            parts = log.split(" ")
            if len(parts) != 7:
                continue
            status = parts[-1]
            if dataset == "hard-gists":
                # uuid
                id = parts[-2][:-1]  # : at the end of id
            results[str(id)] = status.lower()
            if dataset == "github":
                # index as id
                id += 1
        return results

    def parse_dockerizeme_log(self, logs):
        results = dict()
        for log in logs:
            log = log.strip()
            parts = log.split(" ")
            if len(parts) != 2:
                continue
            status = parts[1]
            id = parts[0]
            results[id] = status.lower()
        return results

    def diff(self, other):
        msg = list()
        msg.append("id: {} -- {}".format(self.name, other.name))
        for id in self.results:
            if id not in other.results:
                continue
            other_status = other.results[id]
            status = self.results[id]
            # if status != other_status:
            if status == "success" and other_status != "success" or status != "success" and other_status == "success":
                msg.append("{}: {} -- {}".format(id, status, other_status))
        return msg

    def show(self):
        print(self.name)
        for id in self.results:
            print(id, self.results[id])

    def same(self, other):
        msg = list()
        msg.append("id: {} -- {}".format(self.name, other.name))
        for id in self.results:
            if id not in other.results:
                continue
            other_status = other.results[id]
            status = self.results[id]
            if status == other_status and status == "success":
                msg.append(id)
        return msg


def count_lines(path, line_type):
    if not os.path.exists(path):
        return -1
    file = open(path)
    lines = file.readlines()
    file.close()
    count = 0
    for line in lines:
        if line_type == "all":
            condition = "install" in line and "pip install --upgrade pip" not in line
        else:
            condition = ("pip install" in line or "apt-get install python-" in line or
                         "apt-get install python3-" in line or "[\"pip\",\"install\"" in line) and \
                         "pip install --upgrade pip" not in line
        if condition:
            count += 1
    return count


def count_minus(metadata, path):
    id = path.split(os.sep)[-2]
    try:
        meta = metadata[int(id)]
    except ValueError:
        return 0
    minus = 0
    extra_run_lines = meta["run"]
    for line in extra_run_lines:
        if "pip install" not in line:
            continue
        minus += 1
    return minus


def count_lines_avg(paths, line_type, metadata=None):
    tot = 0
    files_count = len(paths)
    for path in paths:
        if metadata is None:
            minus = 0
        else:
            minus = count_minus(metadata, path)
        count = count_lines(path, line_type) - minus
        if count != -1:
            tot += count
        else:
            files_count -= 1
    avg = 1. * tot / files_count
    return avg


def __count__(root, files, target="Dockerfile", metadata=None):
    paths = [os.path.join(root, file, target) for file in files]
    avg = count_lines_avg(paths, "all", metadata)
    print("avg all pkgs: {:.2f}".format(avg))
    avg = count_lines_avg(paths, "python", metadata)
    print("avg python pkgs: {:.2f}".format(avg))


def count_ego_all(root, metadata=None):
    files = os.listdir(root)
    __count__(root, files, metadata=metadata)


def count_ego_success(root, log_path, dataset="github", metadata=None):
    name = "EGoLog"
    results = TestResults(name, "PyEGo", log_path=log_path, dataset=dataset)

    succ_list = [key for key, value in results.results.items() if value == "success"]
    __count__(root, succ_list, metadata=metadata)


def count_me_all(root, metadata=None):
    files = os.listdir(root)
    __count__(root, files, metadata=metadata)


def count_lines_reqs(path):
    if not os.path.exists(path):
        return -1
    file = open(path)
    lines = file.readlines()
    file.close()
    count = 0
    for line in lines:
        line = line.strip()
        if line != "":
            count += 1
    return count


def count_lines_avg_reqs(paths):
    tot = 0
    files_count = len(paths)
    for path in paths:
        count = count_lines_reqs(path)
        if count != -1:
            tot += count
        else:
            files_count -= 1
    avg = 1. * tot / files_count
    return avg


def __count_reqs__(root, files, target):
    paths = [os.path.join(root, file, target) for file in files]
    avg = count_lines_avg_reqs(paths)
    print("avg python pkgs: {:.2f}".format(avg))


def count_reqs_all(root):
    files = os.listdir(root)
    __count_reqs__(root, files, target="requirements.txt")


def count_reqs_success(root, log_path, log_type="PyEGo"):
    name = "pipreqsLog"
    results = TestResults(name, log_type, log_path=log_path)

    succ_list = [key for key, value in results.results.items() if value == "success"]
    __count_reqs__(root, succ_list, target="requirements.txt")


def count_same_ego_me(ego_root, ego_log_path, me_root, me_log_path, dataset="hard-gists", metadata=None):
    name = "DockerizeMeLog"
    results_me = TestResults(name, "DockerizeMe", log_path=me_log_path)
    name = "EGoLog"
    results_ego = TestResults(name, "PyEGo", log_path=ego_log_path, dataset=dataset)
    same_list = results_me.same(results_ego)[1:]
    print("{} files".format(len(same_list)))

    print("PyEGo:")
    __count__(ego_root, same_list, metadata=metadata)
    print("DockerizeMe:")
    __count__(me_root, same_list, metadata=metadata)


def count_same_ego_reqs(ego_root, ego_log_path, reqs_root, reqs_log_path, reqs_log_type="PyEGo", dataset="github", metadata=None):
    name = "pipreqsLog"
    results_reqs = TestResults(name, reqs_log_type, log_path=reqs_log_path)
    name = "EGoLog"
    results_ego = TestResults(name, "PyEGo", log_path=ego_log_path, dataset=dataset)
    same_list = results_reqs.same(results_ego)[1:]
    print("{} files".format(len(same_list)))

    print("PyEGo:")
    __count__(ego_root, same_list, metadata=metadata)
    print("Pipreqs:")
    __count_reqs__(reqs_root, same_list, target="requirements.txt")
