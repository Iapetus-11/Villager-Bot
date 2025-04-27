# ruff: noqa: T201

import subprocess
import sys


def run_ruff_format(github_output: bool) -> int:
    print("\n\nRunning Ruff formatter...")

    output = subprocess.run(
        ["ruff", "format", ".", *(["--check"] if github_output else [])],
        stdout=(subprocess.PIPE if github_output else None),
    )

    if github_output:
        would_reformat_files = [
            line.removeprefix("Would reformat: ")
            for line in output.stdout.decode().splitlines()
            if line.startswith("Would reformat: ")
        ]

        for file_path in would_reformat_files:
            print(
                f"::error file={file_path},title=isort error::There is an issue with formatting in"
                "this file (not necessarily on line one, run ruff format to fix)",
            )

    return output.returncode


def run_ruff_lint(github_output: bool) -> int:
    print("\n\nRunning Ruff linter...")

    output = subprocess.run(
        [
            "ruff",
            "check",
            ".",
            *(["--output-format", "github"] if github_output else ["--fix"]),
        ],
    )

    return output.returncode


def main():
    github_output = "--github-output" in sys.argv

    return_codes: list[int] = [
        run_ruff_format(github_output),
        run_ruff_lint(github_output),
    ]

    sys.exit(max(return_codes))


if __name__ == "__main__":
    main()
