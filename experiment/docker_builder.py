import os
import docker
import signal


def set_timeout(num):
    def wrap(func):
        def handle(signum, frame):
            raise RuntimeError

        def to_do(*args, **kwargs):
            try:
                signal.signal(signal.SIGALRM, handle)
                signal.alarm(num)
                r = func(*args, **kwargs)
                signal.alarm(0)
                return r
            except RuntimeError:
                raise TimeoutError

        return to_do
    return wrap


def build_image(path, image_name, retry=4):
    dockerfile_path = os.path.join(path, "Dockerfile")
    client = docker.from_env()
    tried = 0
    msg = ""
    while tried < retry:
        try:
            client.images.build(path=path, dockerfile=dockerfile_path, tag=image_name, rm=True)
            return 0, msg
        except Exception as e:
            print(e)
            msg = e.args[0]
            if "returned a non-zero code: 2" not in msg:
                return 1, msg
            print("retry({}/{})".format(tried+1, retry))
            tried += 1
    return 2, msg  # http error


@set_timeout(120)
def run_image(image_name, container_name):
    client = docker.from_env()

    img = client.images.get(image_name)
    ret = 0  # no import error
    msg = ""
    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove(force=True)
    except docker.errors.NotFound:
        pass

    try:
        client.containers.run(img, name=container_name)
    except Exception as e:
        # print(e)
        msg = e.args[0] if len(e.args) > 0 else ""
        msg = str(msg)
        if "ImportError: " in msg or "ModuleNotFoundError: " in msg:
            if "ImportError: attempted relative import with no known parent package" in msg:
                ret = 0  # customize import error
            else:
                ret = 1  # 3rd party import error
        elif isinstance(e, docker.errors.NotFound):
            ret = 1
        else:
            ret = 0
        # ret = 1
    finally:
        try:
            container = client.containers.get(container_name)
            container.stop()
            container.remove(force=True)
            client.images.remove(image_name, force=True)
        except Exception:
            pass
    # print("\n----", ret, "----\n")
    return ret, msg


@set_timeout(60)
def run_image_strict(image_name, container_name):
    client = docker.from_env()

    img = client.images.get(image_name)
    ret = 0  # no import error

    try:
        container = client.containers.get(container_name)
        container.stop()
        container.remove(force=True)
    except docker.errors.NotFound:
        pass

    ret = 0
    msg = None
    try:
        client.containers.run(img, name=container_name)
    except Exception as e:
        msg = e.args[0] if len(e.args) > 0 else ""
        msg = str(msg)
        if msg is None or msg == "":
            ret = 0
        else:
            ret = 1
    finally:
        try:
            container = client.containers.get(container_name)
            container.stop()
            container.remove(force=True)
            client.images.remove(image_name, force=True)
        except Exception:
            pass
    return ret, msg



