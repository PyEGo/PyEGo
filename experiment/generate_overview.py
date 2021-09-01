import csv
import os

from experiment.compare_result import TestResults
from experiment.exp_config import EGO_GISTS_LOG, EGO_GISTS_LOG_2, EGO_GISTS_LOG_3, ME_GISTS_LOG, REQS_GISTS_LOG, \
    EGO_GITHUB_LOG, ME_GITHUB_LOG_39, REQS_GITHUB_LOG_39, EGO_GITHUB_ROOT
from utils import read_object_from_file


def generate_overview(logs, output_path):
    counters = [0 for _ in logs]
    file = open(output_path, "w")
    writer = csv.writer(file)
    names = [log.name for log in logs]
    head = ["id", ]
    for name in names:
        head.append(name)
    writer.writerow(head)

    projects = logs[0].results.keys()
    for project in projects:
        line = [project, ]
        i = 0
        for log in logs:
            results = log.results
            try:
                result = results[project]
                result_ = "√" if result == "success" else "×"
            except KeyError:
                print(log.name, project)
                result_ = "×"
            if result_ == "√":
                counters[i] += 1
            line.append(result_)
            i += 1
        writer.writerow(line)

    overall = ["#√", ]
    for counter in counters:
        overall.append(str(counter))
    writer.writerow(overall)
    file.close()


def generate_gist_overview():
    ego_log = TestResults("PyEGo", "PyEGo", dataset="hard-gists", log_path=EGO_GISTS_LOG)
    ego_log_s2 = TestResults("PyEGo-s2", "PyEGo", dataset="hard-gists", log_path=EGO_GISTS_LOG_2)
    ego_log_s3 = TestResults("PyEGo-s3", "PyEGo", dataset="hard-gists", log_path=EGO_GISTS_LOG_3)
    me_log = TestResults("DockerizeMe", "DockerizeMe", dataset="hard-gists", log_path=ME_GISTS_LOG)
    reqs_log = TestResults("pipreqs", "pipreqs", dataset="hard-gists", log_path=REQS_GISTS_LOG)

    logs = [ego_log, me_log, reqs_log, ego_log_s2, ego_log_s3]
    output = "./result_hard_gists.csv"
    generate_overview(logs, output)


def convert_id_to_name(log, metadata):
    results_ = dict()
    for item in log.results.items():
        # print(item)
        id, result = item[0], item[1]
        name = metadata[int(id)]["name"]
        results_[name] = result
    log.results = results_
    return log


def generate_github_overview():
    ego_log = TestResults("PyEGo", "PyEGo", dataset="github", log_path=EGO_GITHUB_LOG)
    me_log_39 = TestResults("DockerizeMe-3.9", "DockerizeMe", dataset="github", log_path=ME_GITHUB_LOG_39)
    reqs_log_39 = TestResults("pipreqs-3.9", "PyEGo", dataset="github", log_path=REQS_GITHUB_LOG_39)

    logs = [ego_log, me_log_39, reqs_log_39]
    meta_path = os.path.join(EGO_GITHUB_ROOT, "metadata.json")
    metadata = read_object_from_file(meta_path)

    logs_ = list()
    for log in logs:
        log_ = convert_id_to_name(log, metadata)
        logs_.append(log_)
    logs = logs_
    output = "./result_github.csv"
    generate_overview(logs, output)


if __name__ == "__main__":
    generate_gist_overview()
    # generate_github_overview()
