import logging
import os
import multiprocessing
import uuid

from datetime import datetime
from tqdm import tqdm

import config
from experiment.docker_builder import run_image, build_image
from ImportSolver import solve_import

time = datetime.now()
log_name = "hard_gists_test.{}{:02d}{:02d}.log".format(time.year, time.month, time.day)
logging.basicConfig(filename=os.path.join(config.LOG_DIR, log_name),
                    level=logging.INFO, format=config.LOG_FORMAT)


def gene_plain_dockerfile(root):
    dst = os.path.join(root, "Dockerfile")
    file = open(dst, "w")
    lines = ["FROM python:2.7\n", "\n", "ADD snippet.py snippet.py\n", "CMD python snippet.py\n"]
    file.writelines(lines)
    file.close()
    return True


def batch_test(root, process_num=5,
               select_pkgs="select-one", optim_target="approximate", explicit_installed="direct",):
    logging.info("----------START----------")
    # folders = sorted(os.listdir(root))
    folders = os.listdir(root)
    full_paths = [os.path.join(root, folder) for folder in folders]
    queue = multiprocessing.Queue()
    start = 0
    batch_size = len(full_paths)/process_num
    end = int(batch_size)

    processes = list()
    for i in range(process_num-1):
        proc_paths = full_paths[start:end]
        start = end
        end = int(end + batch_size)

        process = multiprocessing.Process(target=batch_test_thread, args=(proc_paths, i, queue, select_pkgs,
                                                                          optim_target, explicit_installed))
        processes.append(process)

    proc_paths = full_paths[start:]
    process = multiprocessing.Process(target=batch_test_thread, args=(proc_paths, process_num-1, queue))
    processes.append(process)

    for process in processes:
        process.start()
    for process in processes:
        process.join()

    succ_count = 0
    for i in range(process_num):
        succ_count += queue.get()

    print("tot {} files".format(len(folders)))
    print("succ {} files".format(succ_count))
    print(1.*succ_count/len(folders))
    logging.info("total: {}/{}, {}".format(succ_count, len(folders), 1.*succ_count/len(folders)))
    logging.info("----------FIN----------")
    print("----------FIN----------")


def batch_test_thread(paths, proc_id=0, queue=None,
                      select_pkgs="select-one", optim_target="approximate", explicit_installed="direct",):
    succ_count = 0
    for folder in tqdm(paths):
        # full_folder = os.path.join(root, folder)
        py_file = os.path.join(folder, "snippet.py")
        message = ""
        result = solve_import(py_file, add_path="snippet.py", cmd_lines=["CMD python snippet.py"],
                              select_pkgs=select_pkgs, optim_target=optim_target, explicit_installed=explicit_installed)
        if not result:
            message = "GenerateFailed"
            logging.warning("<proc{}> {}: {}".format(proc_id, folder.split("/")[-1], message))
            continue

        _, msg = result
        image_name = "image{}".format(proc_id)
        uid = str(uuid.uuid4()).split("-")[0]
        container_name = "contanier{}-{}".format(proc_id, uid)
        ret, result = build_image(folder, image_name)
        if 0 != ret:
            if 1 == ret:
                message = "BuildFailed"
            if 2 == ret:
                message = "HttpError"
            logging.info(result)
        else:
            try:
                ret, result = run_image(image_name, container_name)
                logging.warning(result)
                if 0 == ret:
                    succ_count += 1
                    message = "Success"
                elif 1 == ret:
                    if msg is None:
                        message = "ImportError"
                    else:
                        succ_count += 1
                        message = "ImportError_but_Alerted"
            except TimeoutError:
                message = "Success"  # timeout without import error
        log_level = logging.info if message in ["Success", "ImportError but Alerted"] else logging.warning
        log_level("<proc{}> {}: {}".format(proc_id, folder.split("/")[-1], message))

    print("tot {} files".format(len(paths)))
    print("succ {} files".format(succ_count))
    logging.info("proc{}: {}/{}".format(proc_id, succ_count, len(paths)))
    if queue:
        queue.put(succ_count)
    return succ_count

