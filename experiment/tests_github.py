import os
import argparse
from datetime import datetime

import sys


def find_ego_root():
    config_path = os.path.abspath(__file__)
    parts = config_path.split(os.sep)
    ego_root = os.sep.join(parts[:-2])
    return ego_root


sys.path.append(find_ego_root())

from experiment.statistic_github import statistic_all
from experiment.github_batch_test import batch_test
from experiment.compare_result import count_ego_all, count_reqs_all, count_same_ego_reqs, count_same_ego_me
from experiment.exp_config import EGO_GITHUB_ROOT, EGO_GITHUB_LOG, \
    REQS_GITHUB_ROOT_39, REQS_GITHUB_LOG_39, ME_GITHUB_ROOT_39, ME_GITHUB_LOG_39
from utils import read_object_from_file


def statistic_dataset():
    # statistic [max, min, avg] [python files, LOC, import lines] on github dataset
    print("Statistic Github dataset")
    root = EGO_GITHUB_ROOT
    meta_path = os.path.join(root, "metadata.json")
    metadata = read_object_from_file(meta_path)
    statistic_all(root, metadata)


def run_test_ego():
    # run PyEGo on github dataset, results are logged in log/github_test.<YYYYMMDD>.log
    root = EGO_GITHUB_ROOT
    metadata_path = os.path.join(root, "metadata.json")
    metadata = read_object_from_file(metadata_path)
    batch_test(root, metadata, "PyEGo")


def run_test_pipreqs(pyver="3.8"):
    # run pipreqs on github dataset, results are logged in log/github_test.<YYYYMMDD>.log
    root = REQS_GITHUB_ROOT_39
    metadata_path = os.path.join(root, "metadata.json")
    metadata = read_object_from_file(metadata_path)
    batch_test(root, metadata, "pipreqs", False, pyver)


def test_time_ego():
    # test time cost of PyEGo on github dataset
    root = EGO_GITHUB_ROOT
    metadata_path = os.path.join(root, "metadata.json")
    metadata = read_object_from_file(metadata_path)
    start = datetime.now()
    batch_test(root, metadata, "PyEGo", generate_only=True)
    end = datetime.now()
    cost = end-start
    print("total: {}s, avg: {}s/item".format(cost.seconds, 1.*cost.seconds/100))


def test_time_pipreqs():
    # test time cost of pipreqs on github dataset
    # cannot test here, because os.popen is async function
    start = datetime.now()
    root = REQS_GITHUB_ROOT_39
    metadata_path = os.path.join(root, "metadata.json")
    metadata = read_object_from_file(metadata_path)
    batch_test(root, metadata, "pipreqs", generate_only=True)
    end = datetime.now()
    cost = end-start
    print("total: {}s, avg: {}s/item".format(cost.seconds, 1.*cost.seconds/100))


def statistic_pkgs_ego():
    # statistic pkgs installed in PyEGo-generated Dockerfile
    print("Statistic PyEGo-installed packages")
    ego_root = EGO_GITHUB_ROOT
    meta_path = os.path.join(ego_root, "metadata.json")
    metadata = read_object_from_file(meta_path)
    count_ego_all(ego_root, metadata=metadata)


def statistic_pkgs_me():
    print("Statistic DockerizeMe-installed packages")
    # statistic pkgs installed in DockerizeMe-generated Dockerfile
    me_root = ME_GITHUB_ROOT_39
    ego_root = EGO_GITHUB_ROOT
    meta_path = os.path.join(ego_root, "metadata.json")
    metadata = read_object_from_file(meta_path)
    count_ego_all(me_root, metadata=metadata)


def statistic_pkgs_pipreqs():
    # statistic pkgs installed in pipreqs-generated requirements.txt
    print("Statistic Pipreqs-installed packages")
    reqs_root = REQS_GITHUB_ROOT_39
    count_reqs_all(reqs_root)


def compare_pkgs_ego_me():
    # statistic pkgs installed in projects which solved by both PyEGo and DockerizeMe
    # require execute logs of PyEGo and DockerizeMe
    # Results of DockerizeMe-3.8 and DockerizeMe-3.9 are the same
    print("Compare PyEGo with DockerizeMe")
    ego_root = EGO_GITHUB_ROOT
    ego_log = EGO_GITHUB_LOG
    me_root = ME_GITHUB_ROOT_39
    me_log = ME_GITHUB_LOG_39
    meta_path = os.path.join(ego_root, "metadata.json")
    metadata = read_object_from_file(meta_path)
    count_same_ego_me(ego_root, ego_log, me_root, me_log, dataset="github", metadata=metadata)


def compare_pkgs_ego_pipreqs():
    # statistic pkgs installed in projects which solved by both PyEGo and pipreqs
    # require execute logs of PyEGo and pipreqs
    print("Compare Pipreqs-3.9 with DockerizeMe")
    ego_root = EGO_GITHUB_ROOT
    ego_log = EGO_GITHUB_LOG
    reqs_root = REQS_GITHUB_ROOT_39
    reqs_log = REQS_GITHUB_LOG_39
    meta_path = os.path.join(ego_root, "metadata.json")
    metadata = read_object_from_file(meta_path)
    count_same_ego_reqs(ego_root, ego_log, reqs_root, reqs_log, metadata=metadata)


parser = argparse.ArgumentParser(
    description="Experiment on Github dataset"
)
group = parser.add_mutually_exclusive_group()
group.add_argument('--run', action='store_true')
group.add_argument('--compare', action='store_true')
parser.add_argument('--tool', choices={"PyEGo", "Pipreqs"})
parser.add_argument('--pyver', choices={"3.8", "3.9"}, default="3.8")


if __name__ == "__main__":
    args = parser.parse_args()
    if args.run:
        print("-----Run-----")
        if args.tool == "PyEGo":
            run_test_ego()
        elif args.tool == "Pipreqs":
            run_test_pipreqs(args.pyver)
    elif args.compare:
        print("-----Compare-----")
        statistic_pkgs_ego()
        statistic_pkgs_me()
        statistic_pkgs_pipreqs()
        print("-----Compare with DockerizeMe-----")
        compare_pkgs_ego_me()
        print("-----Compare with Pipreqs-----")
        compare_pkgs_ego_pipreqs()
