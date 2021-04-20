import argparse

from ImportSolver import solve_import


parser = argparse.ArgumentParser(
    description="PyEGo: Runtime Environment Dependency Inference for Python Programs"
)
parser.add_argument("-t", "--output_type", choices={"Dockerfile", "json"}, default="Dockerfile",
                    help="The output type of result, 'Dockerfile' or 'json', default is Dockerfile")
parser.add_argument("-p", "--output_path", default=None,
                    help="The output path of result, default is /program/root/Dockerfile|dependency.json")
parser.add_argument("-r", "--program_root", required=True,
                    help="The code root of Python Programs")

if __name__ == "__main__":
    args = parser.parse_args()
    result = solve_import(args.program_root, dst_path=args.output_path, output_type=args.output_type)
    if result is None:
        print("Generate Failed")
    else:
        print("OK! {} is generated at {}".format(args.output_type, result[0]))
