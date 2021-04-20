import os
import json


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


metadata = read_object_from_file("../GithubTest/metadata.json")
script = open("add_script.sh", "w")

for meta in metadata:
    url = meta["url"]
    id = meta["id"]
    name = meta["name"]
    command = "git submodule add {} ../GithubTest/{}/{}\n".format(url, id, name)
    script.write(command)
    command = "git submodule add {} ../GithubTest-pipreqs/{}/{}\n".format(url, id, name)
    script.write(command)

script.close()
