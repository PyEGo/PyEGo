import os


installed = ["adduser",
             "apt",
             "base-files",
             "base-passwd",
             "bash",
             "bsdutils",
             "coreutils",
             "dash",
             "debconf",
             "debian-archive-keyring",
             "debianutils",
             "diffutils",
             "dpkg",
             "e2fsprogs",
             "fdisk",
             "findutils",
             "gcc-8-base",
             "gpgv",
             "grep",
             "gzip",
             "hostname",
             "init-system-helpers",
             "iproute2",
             "iputils-ping",
             "libacl1",
             "libapt-pkg5.0",
             "libattr1",
             "libaudit-common",
             "libaudit1",
             "libblkid1",
             "libbz2-1.0",
             "libc-bin",
             "libc6",
             "libcap-ng0",
             "libcap2-bin",
             "libcap2",
             "libcom-err2",
             "libdb5.3",
             "libdebconfclient0",
             "libelf1",
             "libext2fs2",
             "libfdisk1",
             "libffi6",
             "libgcc1",
             "libgcrypt20",
             "libgmp10",
             "libgnutls30",
             "libgpg-error0",
             "libhogweed4",
             "libidn2-0",
             "liblz4-1",
             "liblzma5",
             "libmnl0",
             "libmount1",
             "libncursesw6",
             "libnettle6",
             "libp11-kit0",
             "libpam-modules-bin",
             "libpam-modules",
             "libpam-runtime",
             "libpam0g",
             "libpcre3",
             "libseccomp2",
             "libselinux1",
             "libsemanage-common",
             "libsemanage1",
             "libsepol1",
             "libsmartcols1",
             "libss2",
             "libstdc++6",
             "libsystemd0",
             "libtasn1-6",
             "libtinfo6",
             "libudev1",
             "libunistring2",
             "libuuid1",
             "libxtables12",
             "libzstd1",
             "login",
             "mawk",
             "mount",
             "ncurses-base",
             "ncurses-bin",
             "passwd",
             "perl-base",
             "sed",
             "sysvinit-utils",
             "tar",
             "tzdata",
             "util-linux",
             "zlib1g"
             ]


def choose_base_image(pip_pkgvers, pyver):
    methods = [x.split("#")[2] for x in pip_pkgvers]
    if "apt" in methods:
        base_image = "debian:10"
    else:
        base_image = "python:{}".format(pyver)
    return base_image


def generate_sys_lines(sys_pkgvers):
    sys_lines = list()
    sys_lines.append("RUN apt-get update")
    for pkgver in sys_pkgvers:
        pkg, ver, _ = pkgver.split("#")
        if pkg in installed:
            continue  # try!
        if ver == "latest":
            expr = pkg
        else:
            expr = "{}={}".format(pkg, ver)
        line = "RUN apt-get install {} -y".format(expr)
        sys_lines.append(line)
    return sys_lines


def generate_py_lines(pip_pkgvers):
    pip_lines = list()
    pip_lines.append("RUN pip install --upgrade pip")
    # tsinghua source to speed up
    pip_lines.append("RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")
    for pkgver in pip_pkgvers:
        pkg, ver, method = pkgver.split("#")
        if method == "pip":
            expr = "{}=={}".format(pkg, ver)
            line = "RUN pip install {}".format(expr)
        else:
            line = "RUN apt-get install {} -y".format(pkg)  # only latest version
        pip_lines.append(line)
    return pip_lines


def generate_py_install_lines(base_image, pyver):
    if base_image != "debian:10":
        return list()
    py_install_lines = list()
    py_install_lines.append("RUN apt-get update")
    if pyver == "2.7":
        py_install_lines.append("RUN apt-get install python python-pip -y")
    else:
        py_install_lines.extend(["RUN apt-get install python3 python3-pip -y",
                                 "RUN cp /usr/bin/python3 /usr/bin/python",
                                 "RUN cp /usr/bin/pip3 /usr/bin/pip"])
    return py_install_lines


def generate_dockerfile(pip_pkgvers, sys_pkgvers, filepath,
                        msg=None, pyver="3.9", extra_run_lines=None, cmd_lines=None):
    if extra_run_lines is None:
        extra_run_lines = list()
    if cmd_lines is None:
        cmd_lines = list()

    lines = list()
    # FROM python:version image
    base_image = choose_base_image(pip_pkgvers, pyver)
    from_line = "FROM {}".format(base_image)
    lines.append(from_line)
    # adapt apt-get update error
    lines.append("RUN sed -i s@/archive.ubuntu.com/@/mirrors.aliyun.com/@g /etc/apt/sources.list")
    lines.append("RUN apt-get clean")
    # if choose debian as base image, install python manually
    py_install_lines = generate_py_install_lines(base_image, pyver)
    lines.extend(py_install_lines)
    # install system packages
    sys_lines = generate_sys_lines(sys_pkgvers)
    lines.extend(sys_lines)
    # install pip packages
    py_lines = generate_py_lines(pip_pkgvers)
    lines.extend(py_lines)
    # ADD files
    target_file = filepath.split(os.sep)[-1]
    # target_file = filepath
    add_line = "ADD {} {}".format(target_file, target_file)
    lines.append(add_line)
    # extra RUN lines
    for line in extra_run_lines:
        if not line.startswith("RUN "):
            line_ = "RUN {}".format(line)
        else:
            line_ = line
        lines.append(line_)
    # CMD comment & customize CMD lines
    comment_lines = list()
    if msg is not None:
        comment_lines.append("# {}".format(msg))
    comment_lines.append("# add CMD command to run your programs here")
    lines.extend(comment_lines)
    for line in cmd_lines:
        if not line.startswith("CMD "):
            line_ = "CMD {}".format(line)
        else:
            line_ = line
        lines.append(line_)
    # append \n
    lines = [line+"\n" for line in lines]
    return lines
