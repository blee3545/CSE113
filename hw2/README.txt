Homework 2 implementation and report draft

The assignment implementations are in the six required headers:
  template/part1/filter.h
  template/part1/bakery.h
  template/part2/fair_mutex.h
  template/part3/coarse_lock_stack.h
  template/part3/rw_lock_stack.h
  template/part3/swaptop_stack.h

The original main.cpp files and Makefiles were left unchanged. Part 1
headers include yield() as required for submission. Part 2 uses writer
preference and the same reader-side locking pattern as the default mutex.
Part 3 retains the original traversal to the tail for every operation.

Deliverables:
  output/pdf/hw2_report_draft.pdf     Seven-page report with actual results
  output/pdf/hw2_report_draft.txt     Editable text copy of the report
  output/hw2_draft_submission.zip    Six required headers plus report PDF

Review the report before submitting. Its results include three runs of
each configuration on native macOS and in the course Docker container.
No throughput trials were discarded. Full histograms and trial counts
are saved as JSON in results/. The report's Part 1 outlier removal is a
diagnostic comparison only; it does not change the reported averages.

Build the original assignment programs inside the course container:
  make -C template/part1
  make -C template/part2
  make -C template/part3
  make -C template/part3 sequential

Run focused correctness tests:
  python3 scripts/verify.py --label docker
  python3 scripts/verify.py --sanitizer --compiler clang++ --label docker

For Docker ThreadSanitizer, start a temporary container with:
  docker run --rm --security-opt seccomp=unconfined \
    -v "$PWD":/assignments -w /assignments \
    reeselevine/cse113:latest \
    python3 scripts/verify.py --sanitizer --compiler clang++ --label docker

The default Docker syscall filter blocked sanitizer initialization;
the temporary unconfined container ran all six focused tests successfully.
All six custom implementations also passed the supplied wrappers compiled
with Clang ThreadSanitizer. See results/docker_wrapper_tsan.txt.
Native sanitizer executables exited with signal 11 before producing test
output with both available Clang versions. This is not reported as a
successful native sanitizer check. Plain native correctness tests passed.

Repeat benchmarks one environment at a time to avoid CPU competition:
  python3 scripts/run_experiments.py --environment native --cores 10 --runs 3
  python3 scripts/run_experiments.py --environment docker --cores 10 --runs 3

Use the second command inside the course container. Native macOS copies
omit the Linux-only affinity calls; the starter files remain unchanged.
The script creates no-yield variants only in temporary directories. It
replaces the selected environment's saved results with the new run data.

Regenerate the report after editing prose in scripts/build_report.py:
  python3 scripts/build_report.py

This requires the reportlab Python package. In this session it was
installed in /tmp/hw1_pydeps, so generation used:
  PYTHONPATH=/tmp/hw1_pydeps python3 scripts/build_report.py

Editing the text copy alone does not update the PDF. After regenerating
the report, also replace the PDF inside the draft submission ZIP.
