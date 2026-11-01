#!/usr/bin/env python3
"""Independent oracle and complete output validation for C (standard library only)."""

import argparse
from collections import deque
from pathlib import Path
import random
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "C" / "Main.java"
ALL_DAYS = 127


def houses(n):
    return [(i, j) for i in range(1, n + 1)
            for j in range(1, (6 if i % 2 else 7) + 1)]


def adjacent(a, b):
    if abs(a[0] - b[0]) != 1:
        return False
    odd, even = (a, b) if a[0] % 2 else (b, a)
    return even[1] in (odd[1], odd[1] + 1)


def oracle(case, weekly_limit=6, reset=True, with_path=False):
    """Explicit tuple BFS; graph edges are tested from the literal definition."""
    n, bans = case
    vertices = houses(n)
    graph = {p: [p] + [q for q in vertices if adjacent(p, q)] for p in vertices}
    start = (1, 1, 0, 0)
    parent = {start: None}
    queue = deque([(start, 0)])
    while queue:
        state, distance = queue.popleft()
        i, j, day, used = state
        if (i, j) == (n, 6):
            if not with_path:
                return distance
            path = []
            while state is not None:
                path.append(state[:2])
                state = parent[state]
            return distance, list(reversed(path))
        for ni, nj in graph[(i, j)]:
            if bans[(ni, nj)] & (1 << day):
                continue
            new_used = used + (ni < i)
            if new_used > weekly_limit:
                continue
            new_day = (day + 1) % 7
            if reset and new_day == 0:
                new_used = 0
            nxt = (ni, nj, new_day, new_used)
            if nxt not in parent:
                parent[nxt] = state
                queue.append((nxt, distance + 1))
    return (-67, None) if with_path else -67


def mask(text):
    return sum(1 << (int(c) - 1) for c in str(text) if c != "0")


def from_rows(rows):
    n = len(rows)
    bans = {}
    for i, row in enumerate(rows, 1):
        values = row.split()
        assert len(values) == (6 if i % 2 else 7), (i, values)
        for j, value in enumerate(values, 1):
            bans[(i, j)] = mask(value)
    return n, bans


def uniform(n, value):
    return n, {p: value for p in houses(n)}


def schedule_for_path(n, path):
    """Only the nightly destinations of a prescribed walk are open."""
    bans = {p: ALL_DAYS for p in houses(n)}
    for night, p in enumerate(path[1:]):
        bans[p] &= ~(1 << (night % 7))
    return n, bans


def fixtures():
    sample = from_rows([
        "16 615 34 175 3651 6124",
        "2647 157 165 542 14 4731 23417",
        "721 3451 572136 16 54 451",
        "46573 12654 7154 2 354 756 17",
        "3562 2673 4 472 25 12",
    ])
    out = [("sample_open", uniform(3, 0), 10),
           ("sample_schedule", sample, 17),
           ("sample_closed_wednesday", uniform(3, mask(3)), -67),
           ("all_closed", uniform(3, ALL_DAYS), -67)]

    start_closed = uniform(3, 0)
    start_closed[1][(1, 1)] = ALL_DAYS
    out.append(("start_can_be_closed_monday", start_closed, 10))
    monday_closed = uniform(3, 0)
    monday_closed[1][(2, 1)] = 1
    monday_closed[1][(2, 2)] = 1
    monday_closed[1][(1, 1)] = 1
    out.append(("first_action_is_monday", monday_closed, -67))

    target_closed = uniform(3, 0)
    target_closed[1][(3, 6)] = ALL_DAYS
    out.append(("target_never_open", target_closed, -67))

    seven_returns = [
        (1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 3), (7, 3), (8, 3),
        (7, 3), (6, 4), (5, 4), (4, 5), (3, 5), (2, 6), (1, 6),
        (2, 6), (3, 6), (4, 6), (5, 6), (6, 6), (7, 6), (8, 6), (9, 6),
    ]
    blocked_week = schedule_for_path(9, seven_returns)
    assert oracle(blocked_week, weekly_limit=7) == 22
    out.append(("seventh_return_in_one_week_is_forbidden", blocked_week, -67))

    # One Monday stay shifts the final return to next Monday: six plus one.
    reset_path = seven_returns[:8] + [seven_returns[7]] + seven_returns[8:]
    boundary = schedule_for_path(9, reset_path)
    assert oracle(boundary, reset=False) == -67
    out.append(("sunday_sixth_return_then_monday_reset", boundary, 23))

    seventh_house_path = [
        (1, 1), (2, 2), (3, 2), (2, 3), (3, 3), (2, 4), (3, 4),
        (2, 5), (3, 5), (2, 6), (1, 6), (2, 7), (3, 6),
    ]
    out.append(("even_street_seventh_house",
                schedule_for_path(3, seventh_house_path), 12))
    return out


def encode(cases, rng):
    lines = [str(len(cases))]
    for n, bans in cases:
        lines.append(str(n))
        for i in range(1, n + 1):
            values = []
            for j in range(1, (6 if i % 2 else 7) + 1):
                digits = [str(day + 1) for day in range(7)
                          if bans[(i, j)] & (1 << day)]
                rng.shuffle(digits)
                values.append("".join(digits) or "0")
            lines.append(" ".join(values))
    return "\n".join(lines) + "\n"


def validate_output(cases, expected, output):
    tokens = iter(output.split())
    for index, ((n, bans), want) in enumerate(zip(cases, expected)):
        try:
            got = int(next(tokens))
        except StopIteration as exc:
            raise AssertionError(f"case {index}: missing answer") from exc
        assert got == want, (index, n, "distance", got, want, bans)
        if got == -67:
            continue
        assert got >= 0
        try:
            streets = [int(next(tokens)) for _ in range(got + 1)]
            numbers = [int(next(tokens)) for _ in range(got + 1)]
        except StopIteration as exc:
            raise AssertionError(f"case {index}: incomplete path") from exc
        path = list(zip(streets, numbers))
        assert path[0] == (1, 1), (index, "start", path[0])
        assert path[-1] == (n, 6), (index, "finish", path[-1])
        returns = 0
        for step, (a, b) in enumerate(zip(path, path[1:])):
            if step % 7 == 0:
                returns = 0
            assert b in bans, (index, step, "nonexistent house", b)
            assert a == b or adjacent(a, b), (index, step, "invalid edge", a, b)
            assert not bans[b] & (1 << (step % 7)), (index, step, "closed", b)
            returns += b[0] < a[0]
            assert returns <= 6, (index, step, "weekly returns", returns)
    assert next(tokens, None) is None, "extra output"


def run_batch(build, cases, expected, rng, timeout=20):
    started = time.perf_counter()
    result = subprocess.run(["java", "-Xmx256m", "-cp", str(build), "Main"],
                            input=encode(cases, rng), text=True,
                            capture_output=True, timeout=timeout, check=True)
    elapsed = time.perf_counter() - started
    assert not result.stderr, result.stderr
    validate_output(cases, expected, result.stdout)
    return elapsed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=670067)
    parser.add_argument("--perf", action="store_true")
    parser.add_argument("--oracle-only", action="store_true")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    fixed = fixtures()
    for label, case, want in fixed:
        assert oracle(case) == want, (label, oracle(case), want)
    if args.oracle_only:
        print(f"Oracle fixtures OK: {len(fixed)}")
        return

    assert SOURCE.is_file(), f"Java implementation is missing: {SOURCE}"
    checked = 0
    java_seconds = 0.0
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="icpc-c-") as directory:
        build = Path(directory)
        subprocess.run(["javac", "--release", "8", "-Xlint:-options",
                        "-d", str(build), str(SOURCE)],
                       check=True)
        batch = []
        expected = []
        total_n = 0

        def flush():
            nonlocal checked, java_seconds, total_n
            if batch:
                java_seconds += run_batch(build, batch, expected, rng)
                checked += len(batch)
                batch.clear()
                expected.clear()
                total_n = 0

        for _, case, want in fixed:
            batch.append(case)
            expected.append(want)
            total_n += case[0]
        for index in range(args.cases):
            n = rng.choice([3, 5, 7, 9, 11, 13])
            p = rng.choice([0.05, 0.2, 0.4, 0.6, 0.75, 0.9])
            case = (n, {v: sum(1 << day for day in range(7)
                              if rng.random() < p) for v in houses(n)})
            want = oracle(case)
            if total_n + n > 4489:
                flush()
            batch.append(case)
            expected.append(want)
            total_n += n
        flush()

        print(f"OK: {checked} cases, seed={args.seed}; "
              f"Java batches {java_seconds:.3f}s; "
              f"total {time.perf_counter() - started:.3f}s")
        if args.perf:
            large_open = uniform(4489, 0)
            seconds = run_batch(build, [large_open], [4488], rng)
            print(f"max n=4489, all open: {seconds:.3f}s (including JVM startup)")
            large_blocked = uniform(4489, 0)
            large_blocked[1][(4489, 6)] = ALL_DAYS
            seconds = run_batch(build, [large_blocked], [-67], rng)
            print(f"max n=4489, unreachable target: {seconds:.3f}s "
                  "(including JVM startup)")
            many_cases = [uniform(3, 0) for _ in range(1496)]
            seconds = run_batch(build, many_cases, [10] * len(many_cases), rng)
            print(f"1496 cases, sum n=4488: {seconds:.3f}s "
                  "(including JVM startup)")


if __name__ == "__main__":
    main()
