#!/usr/bin/env python3
"""Run the PDF's experiment matrix without editing the supplied wrappers."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build(source_dir, macro, output, standard, native=False):
    source = source_dir / "main.cpp"
    if native:
        # The supplied pthread_setaffinity_np API only exists on Linux.
        text = source.read_text()
        text, matches = re.subn(r"void set_affinity\([^)]*\)\s*\{.*?\n\}",
                               "void set_affinity(std::thread &, int) {}", text,
                               flags=re.DOTALL)
        assert matches == 1
        source = output.parent / (output.name + ".cpp")
        source.write_text(text)
    subprocess.run(["g++", "-std=" + standard, "-D" + macro, str(source),
                    "-I", str(source_dir), "-pthread", "-o", str(output)], check=True)


def execute(binary, arguments, record):
    print("Running", record, flush=True)
    try:
        result = subprocess.run([str(binary)] + [str(v) for v in arguments],
                                capture_output=True, text=True, timeout=90, check=True)
        record["stdout"] = result.stdout
        values = {}
        histogram = []
        for line in result.stdout.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                values[key.strip()] = int(value)
            elif line.strip():
                histogram.append(int(line))
        record["counts"] = values
        if histogram:
            assert sum(histogram) == values["total number"]
            record["histogram"] = histogram
            mean = statistics.mean(histogram)
            record["cv_percent"] = 100 * statistics.pstdev(histogram) / mean if mean else None
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
        record["error"] = str(error)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", choices=["native", "docker"], required=True)
    parser.add_argument("--cores", type=int, default=os.cpu_count())
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    path = ROOT / "results" / (args.environment + ".json")
    data = {"environment": args.environment, "platform": platform.platform(),
            "cores": args.cores, "runs": args.runs,
            "compiler": subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
            "affinity": "supplied Linux affinity calls" if args.environment == "docker" else "unavailable on macOS; affinity calls omitted in temporary copies",
            "records": []}
    def save(record):
        data["records"].append(record)
        path.write_text(json.dumps(data, indent=2) + "\n")

    with tempfile.TemporaryDirectory(prefix="hw2-bench-") as temporary:
        scratch = Path(temporary)
        jobs = []
        for yielding in [False, True]:
            part1 = scratch / ("yield" if yielding else "spin")
            part1.mkdir()
            for filename in ["main.cpp", "filter.h", "bakery.h"]:
                text = (ROOT / "template/part1" / filename).read_text()
                if not yielding:
                    text = text.replace("std::this_thread::yield();", ";")
                (part1 / filename).write_text(text)
            for lock, macro in [("cpp", "CPP_MUTEX"), ("filter", "FILTER_MUTEX"), ("bakery", "BAKERY_MUTEX")]:
                # One baseline suffices: the C++ mutex has no custom spin loop.
                if yielding and lock == "cpp":
                    continue
                binary = scratch / (lock + ("_yield" if yielding else "_spin"))
                build(part1, macro, binary, "c++14", args.environment == "native")
                for factor in [1, 2, 4]:
                    for trial in range(1, args.runs + 1):
                        jobs.append((binary, [args.cores * factor],
                                     {"part": 1, "lock": lock, "yield": yielding if lock != "cpp" else None,
                                      "threads": args.cores * factor, "trial": trial}))
        for lock, macro in [("default", "DEFAULT_MUTEX"), ("fair", "FAIR_MUTEX")]:
            binary = scratch / (lock + "_rw")
            build(ROOT / "template/part2", macro, binary, "c++14", args.environment == "native")
            for readers, writers in [(6, 2), (8, 0)]:
                for trial in range(1, args.runs + 1):
                    jobs.append((binary, [readers, writers],
                                 {"part": 2, "lock": lock, "readers": readers, "writers": writers, "trial": trial}))
        for stack, macro in [("coarse", "COARSE_LOCK"), ("rw", "RW_LOCK"), ("swaptop", "SWAPTOP")]:
            binary = scratch / (stack + "_stack")
            build(ROOT / "template/part3", macro, binary, "c++17", args.environment == "native")
            for trial in range(1, args.runs + 1):
                jobs.append((binary, [], {"part": 3, "stack": stack, "trial": trial}))
        for binary, arguments, record in jobs:
            save(execute(binary, arguments, record))
    print("Saved", path, flush=True)


if __name__ == "__main__":
    main()
