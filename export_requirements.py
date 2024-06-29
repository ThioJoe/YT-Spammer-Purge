import subprocess
import sys

COMMAMD = [
    sys.executable,
    "poetry",
    "export",
    "--without-hashes",
    "--without-urls",
    "--output=requirements.txt",
]

def main() -> int:
    response = subprocess.run(COMMAMD, check=False, capture_output=True)
    if response.returncode != 0:
        print("failed")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
