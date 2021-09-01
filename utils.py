import os
import json
from compare_string_version import compareVersion


def read_object_from_file(file_name):
    """
    read an object from file
    :param file_name: the docker_name of target file
    :return: the object
    """
    if not file_name or os.path.exists(file_name) is False:
        # print ("Error read path: [%s]" % file_name)
        return None
    if os.path.isdir(file_name):
        return None
    with open(file_name, 'r') as f:
        try:
            obj = json.load(f)
        except Exception:
            print("Error json: [%s]" % f.read()[0:10])
            return None
    return obj


def write_object_to_file(file_name, target_object):
    """
    write the object to file with json(if the file is exist, this function will overwrite it)
    :param file_name: the docker_name of new file
    :param target_object: the target object for writing
    :return: True if success else False
    """
    dirname = os.path.dirname(file_name)
    find_and_create_dirs(dirname)
    try:
        with open(file_name, "w") as f:
            json.dump(target_object, f, skipkeys=False, ensure_ascii=False, check_circular=True, allow_nan=True, cls=None, indent=True, separators=None, default=None, sort_keys=False)
    except Exception as e:
        print(e)
        return False
    else:
        # logging.info(get_time() + ": Write " + self.docker_save_path + doc_file_name + ".json")
        # print ("Write %s" % file_name)
        return True


def find_and_create_dirs(dir_name):
    """
    find dir, create it if it doesn't exist
    :param dir_name: the docker_name of dir
    :return: the docker_name of dir
    """
    if os.path.exists(dir_name) is False:
        os.makedirs(dir_name)
    return dir_name


def is_valid_pkg_root(pkg_root):
    if not os.path.exists(pkg_root):
        return False
    # all_version_path = os.path.join(pkg_root, config.PY_PACKAGE_ALL_URL_INDEX_NAME)
    # if not os.path.exists(all_version_path):
    #     return False
    # filtered_version_path = os.path.join(pkg_root, config.KG_PY_PACKAGE_VERSION_INDEX_NAME)
    # if not os.path.exists(filtered_version_path):
    #     return False
    return True


def compare_version(v1, v2):
    try:
        result = compareVersion(v1, v2)
    except ValueError:
        return 1
    if "equal" in result:
        return 0
    if "greater" in result:
        return 1
    return -1
