import os
import argparse
from datetime import datetime
from tqdm import tqdm

import sys


def find_ego_root():
    config_path = os.path.abspath(__file__)
    parts = config_path.split(os.sep)
    ego_root = os.sep.join(parts[:-2])
    return ego_root


sys.path.append(find_ego_root())

from experiment.gists_batch_test import batch_test
from experiment.compare_result import count_ego_all, count_me_all, count_reqs_all,\
    count_same_ego_me, count_same_ego_reqs
from experiment.exp_config import EGO_GISTS_ROOT, EGO_GISTS_LOG, ME_GISTS_ROOT, ME_GISTS_LOG,\
    REQS_GISTS_ROOT, REQS_GISTS_LOG
from ImportSolver import solve_import


def run_test_ego():
    # run PyEGo on hard-gists dataset, results are logged in log/hard_gists_test.<YYYYMMDD>.log
    root = EGO_GISTS_ROOT
    batch_test(root)


def run_test_me():
    # run DockerizeMe on hard-gists dataset, using shell instead of Python
    pass


def run_test_reqs():
    # run pipreqs on hard-gists dataset, using shell instead of Python
    pass


def test_time_ego():
    # test time cost of PyEGo on hard-gists(first 100 gists) dataset
    root = EGO_GISTS_ROOT
    folders = sorted(os.listdir(root))
    count = 100
    start = datetime.now()
    for folder in tqdm(folders[:count]):
        snippet_path = os.path.join(root, folder, "snippet.py")
        solve_import(snippet_path, add_path="snippet.py", cmd_lines=["CMD python snippet.py"])
    end = datetime.now()
    cost = end-start
    print("total: {}s, avg: {}s/item".format(cost.seconds, 1.*cost.seconds/100))


def test_time_me():
    # test time cost of DockerizeMe on hard-gists(first 100 gists) dataset, using shell instead of Python
    pass


def test_time_reqs():
    # test time cost of pipreqs on hard-gists(first 100 gists) dataset, using shell instead of Python
    pass


def statistic_pkgs_ego():
    # statistic pkgs installed in PyEGo-generated Dockerfile
    print("PyEGo:")
    ego_root = EGO_GISTS_ROOT
    count_ego_all(ego_root)


def statistic_pkgs_me():
    # statistic pkgs installed in DockerizeMe-generated Dockerfile
    print("DockerizeMe:")
    me_root = ME_GISTS_ROOT
    count_me_all(me_root)


def statistic_pkgs_pipreqs():
    # statistic pkgs installed in pipreqs-generated requirements.txt
    print("Pipreqs:")
    reqs_root = REQS_GISTS_ROOT
    count_reqs_all(reqs_root)


def compare_pkgs_ego_pipreqs():
    # statistic pkgs installed in gists which solved by both PyEGo and pipreqs
    # require execute logs of PyEGo and pipreqs
    ego_root = EGO_GISTS_ROOT
    ego_log = EGO_GISTS_LOG
    reqs_root = REQS_GISTS_ROOT
    reqs_log = REQS_GISTS_LOG
    count_same_ego_reqs(ego_root, ego_log, reqs_root, reqs_log, reqs_log_type="DockerizeMe", dataset="hard-gists")


def compare_pkgs_ego_me():
    # statistic pkgs installed in gists which solved by both PyEGo and pipreqs
    # require execute logs of PyEGo and pipreqs
    ego_root = EGO_GISTS_ROOT
    ego_log = EGO_GISTS_LOG
    me_root = ME_GISTS_ROOT
    me_log = ME_GISTS_LOG
    count_same_ego_me(ego_root, ego_log, me_root, me_log, dataset="hard-gists")


parser = argparse.ArgumentParser(
    description="Experiment on Hard-gists"
)
group = parser.add_mutually_exclusive_group()
group.add_argument('--run', action='store_true')
group.add_argument('--compare', action='store_true')


if __name__ == "__main__":
    # compare_pkgs_ego_me()
    args = parser.parse_args()
    if args.run:
        print("-----Run-----")
        run_test_ego()
    elif args.compare:
        print("-----Compare-----")
        statistic_pkgs_ego()
        statistic_pkgs_me()
        statistic_pkgs_pipreqs()
        print("-----Compare with DockerizeMe-----")
        compare_pkgs_ego_me()
        print("-----Compare with Pipreqs-----")
        compare_pkgs_ego_pipreqs()

