import os


def find_ego_root():
    config_path = os.path.abspath(__file__)
    parts = config_path.split(os.sep)
    ego_root = os.sep.join(parts[:-1])
    return ego_root


EGO_ROOT = find_ego_root()
CACHE_DIR = os.path.join(EGO_ROOT, "cache")
LOG_DIR = os.path.join(EGO_ROOT, "log")
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

STD_TOP_CACHE_PATH = os.path.join(CACHE_DIR, "std_top.json")
PIP_DEPS_CACHE_PATH = os.path.join(CACHE_DIR, "pipdeps.json")

PY_VERSIONS = ["2.7", "3.5", "3.6", "3.7", "3.8", "3.9"]
LOG_FORMAT = "%(asctime)s [%(levelname)s]  %(message)s"

NEO4J_URI = "YOUR NEO4J URI"
NEO4J_PWD = "YOUR NEO4J PASSWORD"
