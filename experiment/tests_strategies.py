import os
import sys
import argparse


def find_ego_root():
    config_path = os.path.abspath(__file__)
    parts = config_path.split(os.sep)
    ego_root = os.sep.join(parts[:-2])
    return ego_root


sys.path.append(find_ego_root())

from experiment.gists_batch_test import batch_test
from experiment.exp_config import EGO_GISTS_ROOT, EGO_GISTS_ROOT_2, EGO_GISTS_ROOT_3


def __test__(root, select_pkgs="select-one", optim_target="approximate", explicit_installed="direct"):
    print("strategy:", select_pkgs, optim_target, explicit_installed)
    batch_test(root, process_num=1, select_pkgs=select_pkgs,
               optim_target=optim_target, explicit_installed=explicit_installed)


def test_strategy1():
    # select-one & approximate & direct (default strategy)
    root = EGO_GISTS_ROOT
    __test__(root)


def test_strategy2():
    # select-all & approximate & direct
    root = EGO_GISTS_ROOT_2
    __test__(root, select_pkgs="select-all")


def test_strategy3():
    # select-one & exact & direct
    root = EGO_GISTS_ROOT_3
    __test__(root, optim_target="exact")


parser = argparse.ArgumentParser(
    description="Experiment running PyEGo with different strategies"
)
parser.add_argument('--strategy', choices={1, 2}, type=int)


if __name__ == "__main__":
    args = parser.parse_args()
    if args.strategy not in range(1, 3):
        print("Invalid strategy")
    else:
        func_name = "test_strategy{}".format(args.strategy)
        func = globals().get(func_name)
        func()

