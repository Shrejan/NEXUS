import subprocess
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
AUI_EXE = BASE_DIR / "cpp" / "AUI.exe"


def run_uia(command, *args):
    result = subprocess.run(
        [str(AUI_EXE), command, *args],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"AUI error:\n{result.stderr}\n{result.stdout}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"AUI returned invalid JSON:\n{result.stdout}"
        )


def observe():
    return run_uia("observe")


def find(name):
    return run_uia("find", name)


def read(name):
    return run_uia("read", name)


def click(name):
    return run_uia("click", name)


def type_text(name, text):
    return run_uia("type", name, text)


def press(key):
    return run_uia("press", key)

def tree(name=None, depth=3):
    args = []

    if name is not None:
        args.append(name)

    args.append(str(depth))

    return run_uia("tree", *args)

def collect_text(node, result=None):
    if result is None:
        result = []

    name = node.get("name", "").strip()

    if name:
        result.append(name)

    for child in node.get("children", []):
        collect_text(child, result)

    return result