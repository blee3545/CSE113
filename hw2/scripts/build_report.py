#!/usr/bin/env python3
"""Generate the report draft and an editable text copy from saved measurements."""
import json
from pathlib import Path
import statistics
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/pdf"
OUT.mkdir(parents=True, exist_ok=True)
DATA = {env: json.loads((ROOT / "results" / (env + ".json")).read_text())
        for env in ["docker", "native"]}
for data in DATA.values():
    assert len(data["records"]) == 66
    assert not any("error" in record for record in data["records"])

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="BodyDraft", fontName="Helvetica", fontSize=10,
                          leading=14, spaceAfter=8))
styles.add(ParagraphStyle(name="SmallDraft", fontName="Helvetica", fontSize=8.4,
                          leading=11, spaceAfter=5))
styles.add(ParagraphStyle(name="CellDraft", fontName="Helvetica", fontSize=8.3,
                          leading=10.5))
styles.add(ParagraphStyle(name="TitleDraft", fontName="Helvetica-Bold", fontSize=20,
                          leading=24, spaceAfter=14))
styles.add(ParagraphStyle(name="HeadingDraft", fontName="Helvetica-Bold", fontSize=13,
                          leading=17, spaceBefore=8, spaceAfter=8))
story, plain = [], []
INK = colors.HexColor("#203448")
BLUE = colors.HexColor("#326D99")
GREEN = colors.HexColor("#408579")


def paragraph(text, style="BodyDraft"):
    story.append(Paragraph(escape(text), styles[style]))
    plain.append(text + "\n")


def heading(text):
    paragraph(text, "HeadingDraft")


def page(title):
    if story:
        story.append(PageBreak())
    paragraph(title, "TitleDraft")


def table(rows, widths, padding=4):
    header_style = ParagraphStyle(name="header", parent=styles["CellDraft"],
                                  textColor=colors.white, fontName="Helvetica-Bold")
    wrapped = [[Paragraph(escape(str(cell)).replace("\n", "<br/>"),
                          header_style if i == 0 else styles["CellDraft"])
                for cell in row] for i, row in enumerate(rows)]
    result = Table(wrapped, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4F7")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
        ("LINEBELOW", (0, 0), (-1, 0), .5, INK),
    ]))
    story.append(result)
    story.append(Spacer(1, 8))
    plain.extend([" | ".join(str(cell).replace("\n", "; ") for cell in row) for row in rows])
    plain.append("\n")


def records(env, part, **criteria):
    return [r for r in DATA[env]["records"] if r["part"] == part and
            all(r.get(key) == value for key, value in criteria.items())]


def mean_count(env, part, key, **criteria):
    group = records(env, part, **criteria)
    assert len(group) == 3
    return statistics.mean(r["counts"][key] for r in group)


def number(value):
    return f"{value:,.0f}"


page("Part 1: Implementing Mutexes")
paragraph("CSE113 Homework 2 - Report draft | Brian Lee | October 14, 2026", "SmallDraft")
heading("Design")
paragraph("The filter lock stores each thread's current level and one victim for each level. A thread moves through levels 1 through N-1. At each level it names itself the victim, then waits while another thread is at least at that level and it is still the victim. Changing its level to zero releases the lock. Each thread has a distinct ID, so only that thread writes its own level entry.")
paragraph("The bakery lock stores a choosing flag and a ticket for each thread. A thread sets its choosing flag, scans all tickets, chooses one larger than the maximum, and clears the flag. It waits for every other thread to finish choosing, then waits for any smaller (ticket, thread ID) pair. IDs break ties when two threads choose the same ticket. A zero ticket means the thread is not competing for the lock.")
paragraph("All shared algorithm entries are atomic and are accessed only through load() and store(), using the default sequentially consistent ordering. There are no atomic read-modify-write operations in either implementation. The number of threads and array pointers are ordinary variables because initialization finishes before workers start. Both submitted headers call std::this_thread::yield() in their waiting loops.")
table([
    ["Function", "Purpose, inputs, outputs, and assumptions"],
    ["mutex()", "No input. Initializes count to zero and pointers to null; the object is not ready to lock until init()."],
    ["init(N)", "Allocates and initializes arrays for N > 0 threads. Returns void. Called with no threads using the mutex."],
    ["lock(id)", "Returns void with exclusive access. Requires a unique ID in [0, N-1], initialization, no recursion, and no bakery ticket overflow."],
    ["unlock(id)", "Returns void after releasing the caller's lock by clearing its level/ticket. Requires a matching lock(id)."],
    ["~mutex()", "Deletes the arrays after all users finish. These objects are not copied, and IDs are not shared between live threads."],
], [92, 412])
heading("Experiment workflow and verification")
paragraph("Each configuration ran three times without ThreadSanitizer. Both the host and course container expose 10 CPUs, so Part 1 uses 10, 20, and 40 threads. The benchmark uses its original nominal one-second loop and 501-acquisition warmup. No throughput trials were excluded. Temporary header copies remove only yield() for the no-yield experiments; submitted headers retain it.", "SmallDraft")
paragraph("Native measurements use macOS on ARM64; temporary benchmark copies omit the Linux-only affinity function. Docker measurements use the existing reeselevine/cse113:latest ARM64 course image with 10 CPUs and the original wrappers, including their affinity calls. Compiler versions and raw output are saved in results/native.json and results/docker.json. Builds use the starter's language standards and no optimization flag.", "SmallDraft")
paragraph("Focused tests passed natively and in Docker. Clang ThreadSanitizer passed all six focused tests and all six supplied custom-implementation wrappers in Docker. The temporary sanitizer container used --security-opt seccomp=unconfined because the default syscall filter blocked sanitizer startup. The original make all, make test, and stack sequential builds also succeeded in Docker; all three supplied sequential checks reported success.", "SmallDraft")

page("Part 1: Results")
paragraph("Throughput is the mean reported total number across three runs. CV is the population standard deviation of a run's per-thread counts divided by their mean, times 100; the table averages the three CV percentages. Lower CV means more even acquisition counts. N/A means all counts are zero, making CV undefined.", "SmallDraft")
for env, label in [("docker", "Course Docker container"), ("native", "Native macOS")]:
    heading(label)
    rows = [["Threads", "Mutex", "Spin behavior", "Mean throughput", "Mean CV (%)"]]
    for threads in [10, 20, 40]:
        for lock, yielding in [("cpp", None), ("filter", False), ("bakery", False), ("filter", True), ("bakery", True)]:
            group = records(env, 1, lock=lock, threads=threads, **{"yield": yielding})
            cvs = [r["cv_percent"] for r in group if r["cv_percent"] is not None]
            cv = f"{statistics.mean(cvs):.2f}" if cvs else "N/A"
            assert len(cvs) in [0, 3]
            rows.append([threads, "C++" if lock == "cpp" else lock.title(),
                         "Baseline" if yielding is None else ("Yield" if yielding else "No yield"),
                         number(statistics.mean(r["counts"]["total number"] for r in group)), cv])
    table(rows, [48, 76, 84, 164, 132], padding=2)
paragraph("The C++ mutex baseline is reused for both spin comparisons because its code does not change. The tables report benchmark counts, not a separately measured wall-clock rate: finishing a pending acquisition can extend execution beyond the nominal interval.", "SmallDraft")

page("Part 1: Histogram Data and Analysis")
heading("Results: representative histograms")
paragraph("Per-thread acquisition counts from the first Docker trial at 10 threads:", "SmallDraft")
groups = [("cpp", None), ("filter", False), ("bakery", False), ("filter", True), ("bakery", True)]
histograms = [records("docker", 1, lock=lock, threads=10, trial=1, **{"yield": yielding})[0]["histogram"]
              for lock, yielding in groups]
table([["Thread ID", "C++", "Filter spin", "Bakery spin", "Filter yield", "Bakery yield"]] +
      [[i] + [number(histogram[i]) for histogram in histograms] for i in range(10)],
      [49, 91, 91, 91, 91, 91])
outlier = records("docker", 1, lock="filter", threads=40, trial=1, **{"yield": False})[0]
h = outlier["histogram"]
largest_id = max(range(len(h)), key=lambda i: h[i])
trimmed = h[:largest_id] + h[largest_id + 1:]
trimmed_cv = 100 * statistics.pstdev(trimmed) / statistics.mean(trimmed)
paragraph("A high-spread case is Docker filter/no-yield with 40 threads, trial 1. Its full histogram (thread IDs 0-39) is: " + ", ".join(map(str, h)) + ".", "SmallDraft")
paragraph(f"For a manual sensitivity check, removing the largest bin (thread {largest_id}, {h[largest_id]} acquisitions) changes CV from {outlier['cv_percent']:.2f}% to {trimmed_cv:.2f}%. This diagnostic does not change the reported throughput or remove any benchmark trial.", "SmallDraft")
heading("Analysis")
paragraph("The C++ mutex has much higher throughput than the custom locks in the Docker runs. The custom algorithms scan shared arrays, and the filter lock repeats that work at N-1 levels. At 10 threads, however, the custom locks generally distribute acquisitions more evenly. Increasing the thread count makes spinning especially costly: the scheduler can pause a thread that other threads need to advance. Yielding gives waiting threads an opportunity to let runnable competitors proceed, which greatly improves the oversubscribed custom-lock results. The native table also shows that the effect depends on the host scheduler; yield is not a guarantee of better throughput in every configuration.")
paragraph("The very large filter/no-yield CV at 40 threads is consistent with uneven scheduling and staggered worker startup. The histogram sensitivity check changes the numerical CV but does not erase the underlying variability; dropping a busy thread can also hide real unfairness. Other likely sources of variation are background activity, the host's different CPU core types, and the short measurement period. The bakery/no-yield Docker runs at 40 threads record zero measured acquisitions: the total acquisitions remain within the 501-event warmup, so zero does not prove deadlock and cannot be described as perfect fairness. I retained all trials, including these zeros and the large histogram bins, to keep the comparison transparent.")

page("Part 2: A Fair Reader-Writer Lock")
heading("Design")
paragraph("The fair lock follows the default lock's structure and adds a waiting_writers counter. One internal std::mutex protects the active-reader count, writer flag, and waiting-writer count. A reader may enter only when no writer is active or waiting. A writer registers itself before waiting, then enters after existing readers leave and no writer is active. Registering a writer closes the gate to new readers, allowing the current readers to drain. When there are no writers, readers follow the default path with only one additional counter check; no condition variables or extra reader-side locks are used. This is writer preference, not a FIFO guarantee: continuous writers can delay readers, and writer ordering depends on scheduling.")
table([
    ["Function", "Purpose, inputs, outputs, and assumptions"],
    ["rw_mutex()", "No input. Initializes reader and waiting-writer counts to zero and writer to false."],
    ["lock_reader()", "No input; returns void once shared access is acquired. Multiple readers can enter. Caller must not already own this lock."],
    ["unlock_reader()", "No input; returns void after decrementing the active-reader count. Requires a matching reader acquisition."],
    ["lock()", "No input; returns void with exclusive writer access. Registers one waiting writer, then removes that registration when admitted."],
    ["unlock()", "No input; returns void after clearing the active-writer flag. Requires a matching writer acquisition."],
], [105, 399])
heading("Results")
paragraph("Each configuration ran three times. The table gives mean reader/writer counts and each count's minimum-to-maximum range. Values are the original wrapper's reported totals; counters are incremented before the lock calls and exclude the wrapper's 2,048-event warmup per role.", "SmallDraft")
rows = [["Environment", "R/W", "Mutex", "Readers: mean\n(min - max)", "Writers: mean\n(min - max)"]]
for env in ["docker", "native"]:
    for readers, writers in [(6, 2), (8, 0)]:
        for lock in ["default", "fair"]:
            group = records(env, 2, lock=lock, readers=readers, writers=writers)
            cells = []
            for key in ["total readers", "total writers"]:
                values = [r["counts"][key] for r in group]
                cells.append(f"{number(statistics.mean(values))}\n({number(min(values))} - {number(max(values))})")
            rows.append([env.title(), f"{readers}/{writers}", lock.title()] + cells)
table(rows, [66, 39, 55, 172, 172])

page("Part 2: Graph and Analysis")
heading("Results: six readers and two writers")
paragraph("Grouped bars show mean reported counts; error bars show the minimum and maximum across three runs. Each panel has its own horizontal scale, and both locks use the same scale within a panel.", "SmallDraft")
drawing = Drawing(504, 270)
for panel, env in enumerate(["docker", "native"]):
    bottom = 142 if panel == 0 else 8
    metrics = []
    for lock in ["default", "fair"]:
        for role, key, color in [("Readers", "total readers", BLUE), ("Writers", "total writers", GREEN)]:
            values = [r["counts"][key] for r in records(env, 2, lock=lock, readers=6, writers=2)]
            metrics.append((lock.title() + " " + role, statistics.mean(values), min(values), max(values), color))
    maximum = max(m[3] for m in metrics) * 1.06
    drawing.add(String(0, bottom + 114, "Course Docker" if env == "docker" else "Native macOS", fontName="Helvetica-Bold", fontSize=11, fillColor=INK))
    for i, (label, mean, low, high, color) in enumerate(metrics):
        y = bottom + 87 - 23 * i
        drawing.add(String(0, y + 3, label, fontName="Helvetica", fontSize=9))
        drawing.add(Rect(93, y, 326 * mean / maximum, 13, fillColor=color, strokeColor=None))
        xlow, xhigh = 93 + 326 * low / maximum, 93 + 326 * high / maximum
        drawing.add(Rect(xlow, y + 5.5, max(xhigh - xlow, .5), 1.5, fillColor=INK, strokeColor=None))
        for x in [xlow, xhigh]: drawing.add(Rect(x, y + 3, .7, 7, fillColor=INK, strokeColor=None))
        drawing.add(String(426, y + 3, number(mean), fontName="Helvetica", fontSize=8.5))
    drawing.add(String(93, bottom, "0", fontName="Helvetica", fontSize=8))
    drawing.add(String(419, bottom, number(maximum), textAnchor="end", fontName="Helvetica", fontSize=8))
story.append(drawing)
plain.append("Graph: grouped reader/writer mean counts with min/max error bars, using the preceding table.\n")
heading("Analysis")
comparison = []
for env in ["docker", "native"]:
    base_w = mean_count(env, 2, "total writers", lock="default", readers=6, writers=2)
    fair_w = mean_count(env, 2, "total writers", lock="fair", readers=6, writers=2)
    base_r = mean_count(env, 2, "total readers", lock="default", readers=8, writers=0)
    fair_r = mean_count(env, 2, "total readers", lock="fair", readers=8, writers=0)
    comparison.append(f"{env.title()}: writer counts increase {fair_w/base_w:.2f} times, while the reader-only mean changes by {(fair_r/base_r-1)*100:+.2f}%")
paragraph("; ".join(comparison) + ". The much larger writer count and lower reader count in the mixed workload agree with the design: readers cannot repeatedly bypass waiting writers. In the no-writer workload, waiting_writers remains zero, so shared reader admission stays close to the default behavior. Short runs and the reported ranges limit how precisely a small reader-only difference can be interpreted. The lock improves access for the writer group but does not measure fairness between individual writers or prove a starvation bound. Native and Docker absolute rates differ because their mutex implementations and scheduling environments differ, and native affinity was unavailable.")
heading("Verification and reproduction")
paragraph("The focused reader-writer test first requires two readers to hold the lock together. Its mixed phase checks that writers never overlap readers or other writers and that two writers complete exactly 6,000 updates. The tests use atomic counters for observations; the protected payload remains ordinary memory so ThreadSanitizer can detect a synchronization failure.", "SmallDraft")
paragraph("Reproduce measurements with python3 scripts/run_experiments.py --environment native --cores 10 --runs 3, or run the same script with --environment docker inside the course container. Compile and run checks with python3 scripts/verify.py; for the sanitizer use --sanitizer --compiler clang++. Raw counts, histograms, compiler versions, and test logs are in results/.", "SmallDraft")

page("Part 3: A Concurrent Linked List")
heading("Design")
paragraph("All three stacks keep the original representation: start points to the first node, and the last node is the stack top. Every nonempty operation begins at start and traverses next pointers to the tail; there is no cached tail pointer and no reversal of the list. A node stores its integer value and next pointer. push appends, pop removes the last node, and peek reads the last node. The allowed input values are 0, 1, and 2.")
paragraph("The coarse stack holds one std::mutex for each complete push, pop, or peek, including traversal. The reader-writer stack uses one std::shared_mutex: push and pop hold it exclusively because they change links or destroy nodes, while peek holds it in shared mode so several readers can traverse together. Scoped lock objects release the lock even when an empty or single-node branch returns early. Holding the lock throughout traversal prevents a writer from deleting a node that a reader still uses.")
paragraph("SwapTop keeps the reader-writer stack's push, pop, and peek unchanged. It first takes a shared lock and traverses to the last node. If the list is empty, it returns; if the existing value equals the requested value, it also returns because there is no write to perform. The three-value input domain makes this shortcut useful, and the benchmark heavily favors zero. Otherwise it releases the shared lock, acquires an exclusive lock, checks for an empty list again, traverses again, and replaces the current tail's value. It never keeps a node pointer across the unlocked interval, since a concurrent pop could delete that node. The no-change case takes effect at the shared-lock observation, and the changing case takes effect at the exclusive-lock assignment.")
table([
    ["Function", "Purpose, inputs, outputs, and assumptions"],
    ["Llist_node(d)", "Creates a node with integer d and next = null. Nodes are allocated/linked only while holding the stack's writer/exclusive lock."],
    ["CSE113_Stack()", "No input. Creates an empty stack by setting start to null, before worker threads launch."],
    ["push(p)", "Requires p in {0,1,2}; returns void after appending one node at the tail."],
    ["pop()", "No input; removes and returns the tail value, or -1 when empty. Handles the single-node case by clearing start."],
    ["peek()", "No input; returns the tail value without removing it, or -1 when empty."],
    ["swaptop(v)", "Only in the third stack. Requires v in {0,1,2}; returns void after replacing the current top, or does nothing when empty."],
], [113, 391])
heading("Experiment workflow and correctness")
paragraph("Each stack ran exactly three times per environment, starting with 1,024 nodes. Coarse and RW use four peekers, one popper, and one pusher. SwapTop adds four swaptoppers, so it has ten workers rather than six. Counts include attempted empty operations, not just successful pops. The benchmark generates zero with probability 997/1000 and one otherwise; value two is covered by correctness tests.", "SmallDraft")
paragraph("The tests check empty behavior, all legal values, LIFO order, changing and unchanged SwapTop calls, preservation of 600 concurrently pushed nodes, and mixed concurrent operations. The supplied sequential checks and Clang ThreadSanitizer wrappers also pass in the course container.", "SmallDraft")

page("Part 3: Results and Analysis")
heading("Results")
paragraph("Mean operation counts over three runs; parentheses give each operation's minimum and maximum. Totals include all operation types for that stack. A dash means SwapTop is not part of the implementation.", "SmallDraft")
for env, label in [("docker", "Course Docker"), ("native", "Native macOS")]:
    heading(label)
    rows = [["Stack", "Total", "Peek", "Pop", "Push", "SwapTop"]]
    for stack in ["coarse", "rw", "swaptop"]:
        group = records(env, 3, stack=stack)
        row = [stack.title()]
        for key in ["total operations", "total peeks", "total pops", "total pushes", "total swaptops"]:
            if key not in group[0]["counts"]:
                row.append("-")
            else:
                values = [r["counts"][key] for r in group]
                row.append(f"{number(statistics.mean(values))}\n({number(min(values))}\n- {number(max(values))})")
        rows.append(row)
    table(rows, [57, 90, 90, 86, 86, 95], padding=2)
heading("Analysis")
docker_coarse = mean_count("docker", 3, "total operations", stack="coarse")
docker_rw = mean_count("docker", 3, "total operations", stack="rw")
docker_peek_ratio = mean_count("docker", 3, "total peeks", stack="rw") / mean_count("docker", 3, "total peeks", stack="coarse")
native_ratio = mean_count("native", 3, "total operations", stack="rw") / mean_count("native", 3, "total operations", stack="coarse")
paragraph(f"In Docker, the RW stack's mean total is {docker_rw/docker_coarse:.2f} times the coarse stack's, and its mean peek count is {docker_peek_ratio:.2f} times as large. This agrees with the expected benefit of allowing four peekers to traverse at once. On the native host, the RW/coarse total ratio is {native_ratio:.2f}, showing that the exact benefit depends on the implementation and scheduler. Each traversal is still O(list length), so changes in stack depth can substantially change the cost of later operations. Docker coarse trial 1 reports 419,315 operations, compared with 173,436 and 172,401 in trials 2 and 3. This is a large spread, so the three-run average should not be treated as a precise stable rate; all three values remain in the average.")
paragraph("The SwapTop shortcut can share the read lock with peekers when the requested value already matches the tail. The benchmark's strong preference for zero makes this case more common than a uniform choice among three values would, so its throughput is specific to this workload. Actual changes require exclusive access and a second traversal; that adds work and competition with push and pop. The reported per-operation ranges show substantial variation in some runs. SwapTop also adds four workers and a new counted operation, so comparing its total directly with the six-worker stacks would confound algorithm behavior with workload size. Atomic benchmark counters, random-value generation, sleeping, background scheduling, and changing stack depth all contribute to the observed rates.")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(54, 29, "CSE113 Homework 2 | Report draft")
    canvas.drawRightString(558, 29, str(doc.page))
    canvas.restoreState()


pdf = OUT / "hw2_report_draft.pdf"
doc = SimpleDocTemplate(str(pdf), pagesize=(612, 792), leftMargin=54,
                        rightMargin=54, topMargin=42, bottomMargin=47,
                        title="CSE113 Homework 2 - Report Draft", author="Brian Lee")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
(OUT / "hw2_report_draft.txt").write_text("\n".join(plain) + "\n")
print("Created", pdf)
