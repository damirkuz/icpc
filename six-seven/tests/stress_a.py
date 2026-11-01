#!/usr/bin/env python3
"""Independent black-box checks for A. Uses recurrence cycles / fast doubling."""

import argparse
import random
import subprocess
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_Q = 67 ** 3
U64 = 1 << 64


def recurrence_cycle(k):
    """Discover the period directly, without the solution's lifting formula."""
    modulus = 1 << k
    first = (6 % modulus, 7 % modulus)
    a, b = first
    values = []
    while True:
        values.append(a)
        a, b = b, (a + b) % modulus
        if (a, b) == first:
            return values
        if len(values) > 6 * modulus:
            raise AssertionError("Unexpectedly long brute-force period")


def value_fast_doubling(n, k):
    """F_n = f_n + 6 f_(n+1), using unbounded Python integers."""
    modulus = 1 << k
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = a * (2 * b - a) % modulus
        d = (a * a + b * b) % modulus
        if bit == "0":
            a, b = c, d
        else:
            a, b = d, (c + d) % modulus
    return (a + 6 * b) % modulus


def run_java(build_dir, queries):
    assert 1 <= len(queries) <= MAX_Q
    data = str(len(queries)) + "\n" + "".join(
        f"{k} {x}\n" for k, x in queries
    )
    start = time.perf_counter()
    result = subprocess.run(
        ["java", "-Xmx256m", "-cp", str(build_dir), "Main"],
        input=data,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=60,
    )
    elapsed = time.perf_counter() - start
    assert not result.stderr, result.stderr
    tokens = result.stdout.split()
    assert len(tokens) == len(queries), (len(tokens), len(queries))
    answers = [int(token) for token in tokens]
    return answers, elapsed


def check_answers(queries, answers, cycles=None):
    reachable = ({k: set(values) for k, values in cycles.items()}
                 if cycles is not None else None)
    for position, ((k, x), n) in enumerate(zip(queries, answers), 1):
        # In this problem every odd target has a solution. Small cases also
        # establish existence by exhaustive enumeration, independently.
        assert n != -67, f"query {position}: k={k}, x={x}: unexpected -67"
        assert 0 <= n < U64, (position, k, x, n)
        if cycles is not None:
            cycle = cycles[k]
            assert x in reachable[k], (k, x)
            actual = cycle[n % len(cycle)]
        else:
            actual = value_fast_doubling(n, k)
        assert actual == x, (
            f"query {position}: k={k}, x={x}, n={n}, F_n mod 2^k={actual}"
        )


def check_reference():
    # Protect the independent checker with direct, hand-known sequence values.
    known = [6, 7, 13, 20, 33, 53, 86, 139, 225, 364, 589]
    for n, value in enumerate(known):
        for k in range(1, 12):
            assert value_fast_doubling(n, k) == value % (1 << k)
    for k in range(1, 9):
        cycle = recurrence_cycle(k)
        for n, value in enumerate(cycle):
            assert value_fast_doubling(n, k) == value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--small-k", type=int, default=14)
    parser.add_argument("--random", type=int, default=20000)
    parser.add_argument("--performance", action="store_true")
    parser.add_argument("--seed", type=int, default=676767)
    args = parser.parse_args()
    assert 1 <= args.small_k <= 18
    rng = random.Random(args.seed)
    check_reference()

    with tempfile.TemporaryDirectory(prefix="icpc-a-") as temporary:
        build_dir = Path(temporary)
        subprocess.run(
            ["javac", "--release", "8", "-Xlint:-options", "-d", str(build_dir),
             str(ROOT / "A" / "Main.java")],
            check=True,
        )

        cycles = {k: recurrence_cycle(k) for k in range(1, args.small_k + 1)}
        queries = [(k, x) for k in cycles for x in range(1, 1 << k, 2)]
        answers, elapsed = run_java(build_dir, queries)
        check_answers(queries, answers, cycles)
        print(f"PASS exhaustive: {len(queries)} queries, k<= {args.small_k}, "
              f"Java {elapsed:.3f}s")

        queries = [(59, 676767), (7, 67)]
        for k in range(1, 61):
            modulus = 1 << k
            targets = {1, 3 % modulus, 7 % modulus, modulus - 1,
                       (modulus // 2) | 1, (modulus // 2 - 1) | 1}
            queries.extend((k, x) for x in sorted(targets) if 0 < x < modulus)
        # These forward-generated targets force consecutive corrections of
        # every remaining bit in the solution's chosen branch.
        for k in range(2, 61):
            for base in (1, 2):
                n = (3 << (k - 1)) - 6 + base
                queries.append((k, value_fast_doubling(n, k)))
        for _ in range(args.random):
            k = rng.randint(1, 60)
            queries.append((k, rng.getrandbits(k) | 1))
        # Derive targets from indices across the entire permitted uint64 range.
        source_indices = [1, 2, (1 << 63) - 1, 1 << 63, U64 - 2]
        source_indices.extend(rng.getrandbits(64) for _ in range(args.random // 2))
        for n in source_indices:
            if n % 3 == 0:
                n += -1 if n == U64 - 1 else 1
            k = rng.randint(1, 60)
            queries.append((k, value_fast_doubling(n, k)))
        answers, elapsed = run_java(build_dir, queries)
        check_answers(queries, answers)
        print(f"PASS boundaries/random: {len(queries)} queries, seed={args.seed}, "
              f"Java {elapsed:.3f}s")

        if args.performance:
            queries = [(60, rng.getrandbits(60) | 1) for _ in range(MAX_Q)]
            answers, elapsed = run_java(build_dir, queries)
            validation_start = time.perf_counter()
            check_answers(queries, answers)
            validation_elapsed = time.perf_counter() - validation_start
            print(f"PASS maximum q: {len(queries)} queries, all k=60, "
                  f"Java {elapsed:.3f}s, independent validation "
                  f"{validation_elapsed:.3f}s")

            target = value_fast_doubling((3 << 59) - 4, 60)
            queries = [(60, target)] * MAX_Q
            answers, elapsed = run_java(build_dir, queries)
            check_answers(queries, answers)
            print(f"PASS maximum q, every lifting step: {len(queries)} queries, "
                  f"Java {elapsed:.3f}s")


if __name__ == "__main__":
    main()
