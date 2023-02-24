import os

SYSTEM_CMDS = [
    "poetry run autoflake --remove-all-unused-imports --expand-star-imports --ignore-init-module-imports --in-place --recursive bot/ common/ karen/ scripts/",
    "poetry run isort .",
    "poetry run black .",
]


def run():
    for cmd in SYSTEM_CMDS:
        os.system(cmd)


if __name__ == "__main__":
    run()
