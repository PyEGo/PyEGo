# json format:
# {
#     python_version: "2.7",
#     system_lib: [
#         {
#             name: "libopencv-core3.2",
#             version: "latest",
#             install_method: "apt",
#         },
#         {}
#     ],
#     python_packages: [
#         {
#             name: "",
#             version: "",
#             install_method: ""
#         },
#         {}
#     ],
#     message: ""
# }


def generate_json(pkgvers, sys_pkgs, pyver, msg):
    j = dict()
    j["python_version"] = pyver
    j["system_lib"] = list()
    for lib in sys_pkgs:
        name, version, method = lib.split("#")
        j["system_lib"].append({"name": name, "version": version, "install_method": method})
    j["python_packages"] = list()
    for pkg in pkgvers:
        name, version, method = pkg.split("#")
        j["python_packages"].append({"name": name, "version": version, "install_method": method})
    j["message"] = msg
    return j
