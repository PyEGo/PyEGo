import logging
import os

from datetime import datetime
from tqdm import tqdm

import config
from experiment.docker_builder import run_image_strict, build_image
from ImportSolver import solve_import
from experiment.exp_config import PIPREQS_PATH

time = datetime.now()
log_name = "github_test.{}{:02d}{:02d}.log".format(time.year, time.month, time.day)
logging.basicConfig(filename=os.path.join(config.LOG_DIR, log_name),
                    level=logging.INFO, format=config.LOG_FORMAT)


class TestCase:
    def __init__(self, metadata, test_root):
        self.ind = metadata['id']
        self.name = metadata['name']
        self.url = metadata['url']
        self.desc = metadata['desc']
        self.project_type = metadata['project_type']
        self.tags = metadata['tag']
        self.code_root = os.path.join(test_root, metadata['coderoot'])
        self.folder = os.path.join(test_root, str(self.ind))
        self.run_lines = metadata['run']
        self.cmd_line = metadata['cmd']

    def run_test(self, generate_only=False):
        dockerfile_path = os.path.join(self.folder, "Dockerfile")
        result = solve_import(self.code_root, dst_path=dockerfile_path, add_path=self.name,
                              extra_run_lines=self.run_lines, cmd_lines=[self.cmd_line])
        if not result:
            return 1  # GenerateFailed

        if generate_only:
            return 0  # only generate Dockerfile

        _, msg = result
        image_name = "image{}".format(self.ind)
        ret, result = build_image(self.folder, image_name)
        if 1 == ret:
            return 2   # BuildFailed
        if 2 == ret:
            return 3  # HttpError

        container_name = "contanier{}".format(self.ind)
        try:
            result, msg = run_image_strict(image_name, container_name)
            if 0 == result or msg == "":
                return 0  # Success
            if 1 == result and "ImportError" in msg or "ModuleNotFoundError" in msg or "SyntaxError" in msg:
                logging.error(msg)
                return 4  # RunFailed
            else:
                logging.error(msg)
                return 5  # Safe?

        except TimeoutError:
            return 0

    def run_test_pipreqs(self, pyver="3.8", generate_only=False):
        req_path = os.path.join(self.folder, "requirements.txt")
        cmd = "cd {} && {} . --force".format(self.code_root, PIPREQS_PATH)
        os.popen(cmd)
        cmd = "cd {} && cp requirements.txt {}".format(self.code_root, req_path)
        os.popen(cmd)

        if generate_only:
            return 0  # only generate requirements.txt

        dockerfile_path = os.path.join(self.folder, "Dockerfile")
        lines = ["FROM python:{}\n".format(pyver),
                 "RUN apt-get update\n",
                 "ADD requirements.txt requirements.txt\n",
                 "RUN pip install -r requirements.txt\n",
                 "ADD {} {}\n".format(self.name, self.name)]
        for cmd in self.run_lines:
            lines.append("RUN {}\n".format(cmd))
        lines.append("CMD {}\n".format(self.cmd_line))
        with open(dockerfile_path, "w") as f:
            f.writelines(lines)

        image_name = "image{}".format(self.ind)
        result, msg = build_image(self.folder, image_name)
        print(msg)
        if 1 == result:
            return 2   # BuildFailed
        if 2 == result:
            return 3  # HttpError

        container_name = "contanier{}".format(self.ind)
        try:
            result, msg = run_image_strict(image_name, container_name)
            if 0 == result or msg == "":
                return 0  # Success
            if 1 == result and "ImportError" in msg or "ModuleNotFoundError" in msg or "SyntaxError" in msg:
                logging.error(msg)
                return 4  # RunFailed
            else:
                logging.error(msg)
                return 5  # Safe?

        except TimeoutError:
            return 0


def batch_test(test_root, metadata, test_tool="PyEGo", generate_only=False, pyver="3.8"):
    info_dict = {
        0: "Success",
        1: "GenerateFailed",
        2: "BuildFailed",
        3: "HttpError",
        4: "RunFailed",
        5: "Safe"
    }
    tot = len(metadata)
    succ_count = 0

    logging.info("----------START----------")
    for item in tqdm(metadata):
        case = TestCase(item, test_root)
        if test_tool == "pipreqs":
            ret = case.run_test_pipreqs(pyver, generate_only)
        else:
            ret = case.run_test(generate_only)
        msg = "<proc0> {}: {}".format(case.name, info_dict[ret])
        if 0 == ret:
            succ_count += 1
            logging.info(msg)
        else:
            logging.error(msg)
    logging.info("{}/{}, {}".format(succ_count, tot, (1.*succ_count/tot)))
    logging.info("----------END----------")



