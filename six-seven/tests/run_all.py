#!/usr/bin/env python3
"""Compile all three standalone Java solutions and run the full local checks."""
from pathlib import Path
import subprocess
import sys
import time


def main():
    tests = Path(__file__).resolve().parent
    commands = [
        ("stress_a.py", "--small-k", "18", "--random", "50000", "--performance"),
        ("stress_b.py",),
        ("stress_c.py", "--cases", "4000", "--perf"),
    ]
    start = time.perf_counter()
    for script, *arguments in commands:
        print(f"Running {script}", flush=True)
        subprocess.run([sys.executable, "-u", str(tests / script), *arguments], check=True)
    print(f"All local checks passed in {time.perf_counter() - start:.3f}s", flush=True)


if __name__ == "__main__":
    main()
