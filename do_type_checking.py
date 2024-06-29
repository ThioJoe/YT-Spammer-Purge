"""Run the type checking tools."""

import pathlib
import subprocess
import sys


def get_python_binary() -> str:
    return sys.executable


def main() -> int:
    pybin = get_python_binary()
    curdir = pathlib.Path.cwd()
    print("running pyright...")
    pyright_response = subprocess.run(
        [pybin, "-m", "pyright", str(curdir)], check=False, capture_output=True
    )
    if pyright_response.returncode != 0:
        print("error on pyright:")
        print(pyright_response.stderr.decode("utf-8"))
        return 1
    with pathlib.Path("pyright_results.txt").open("wb") as file:
        file.write(pyright_response.stdout)

    print("running ruff...")
    ruff_response = subprocess.run(
        [pybin, "-m", "pyright", str(curdir)], check=False, capture_output=True
    )
    if ruff_response.returncode != 0:
        print("error on ruff:")
        print(ruff_response.stderr.decode("utf-8"))
        return 1
    with pathlib.Path("ruff_results.txt").open("wb") as file:
        file.write(ruff_response.stdout)
    print("process finished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
