#!/usr/bin/env python3
"""Compile focused concurrency tests, optionally with ThreadSanitizer."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--sanitizer", action="store_true")
parser.add_argument("--compiler", default="g++")
parser.add_argument("--label", default="native")
args = parser.parse_args()
cases = [("filter", 1, "filter.h"), ("bakery", 1, "bakery.h"),
         ("fair", 2, "fair_mutex.h"), ("coarse", 3, "coarse_lock_stack.h"),
         ("rw", 3, "rw_lock_stack.h"), ("swaptop", 3, "swaptop_stack.h")]
results = []
with tempfile.TemporaryDirectory(prefix="hw2-tests-") as temporary:
    for name, part, header in cases:
        binary = Path(temporary) / name
        command = [args.compiler, "-std=c++17" if part == 3 else "-std=c++14",
                   "-pthread", "-g", "-Wall", "-Wextra", "-pedantic",
                   '-DTEST_HEADER="' + header + '"',
                   "-I", str(ROOT / "template" / ("part" + str(part))),
                   str(ROOT / "tests" / ("test_part" + str(part) + ".cpp")), "-o", str(binary)]
        if name == "swaptop": command.append("-DTEST_SWAPTOP")
        if args.sanitizer: command.append("-fsanitize=thread")
        record = {"case": name, "command": command}
        print("Testing", name, "TSan" if args.sanitizer else "plain", flush=True)
        try:
            compile_result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True)
            record["compiler_output"] = compile_result.stdout + compile_result.stderr
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=90)
            record.update(returncode=run.returncode, stdout=run.stdout, stderr=run.stderr)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
            record["error"] = str(error)
            record["stderr"] = getattr(error, "stderr", "")
        results.append(record)
        print(record.get("stdout", "") + record.get("stderr", ""), flush=True)
path = ROOT / "results" / (args.label + ("_tsan" if args.sanitizer else "_tests") + ".json")
path.write_text(json.dumps(results, indent=2) + "\n")
if any(record.get("returncode") != 0 for record in results):
    raise SystemExit(1)
