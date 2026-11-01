#!/usr/bin/env python3
"""Independent Roman-number generator and local interactive judge for B."""
import argparse
from pathlib import Path
import random
import selectors
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
ROMAN = ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
         (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
         (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))


def roman(value):
    result = []
    for number, text in ROMAN:
        count, value = divmod(value, number)
        result.append(text * count)
    return "".join(result)


def all_strings(digits):
    if not digits:
        yield ""
        return
    for length in range(1, min(4, len(digits)) + 1):
        value = int(digits[:length])
        if value > 3999:
            break
        for suffix in all_strings(digits[length:]):
            yield roman(value) + suffix


def positions(s):
    return tuple(i for i, c in enumerate(s) if c == "I")


def replies(s):
    original = positions(s)
    yield original
    for i in range(len(original)):
        for delta in (-1, 1):
            changed = list(original)
            changed[i] += delta
            yield tuple(sorted(changed))


def random_string(rng, n):
    digits = "67" * n
    result = []
    offset = 0
    while offset < len(digits):
        length = rng.randint(1, min(3, len(digits) - offset))
        result.append(roman(int(digits[offset:offset + length])))
        offset += length
    return "".join(result)


HARNESS = """
import java.io.*;
public class BDecoderHarness {
    public static void main(String[] args) throws Exception {
        StreamTokenizer in = new StreamTokenizer(new BufferedReader(new InputStreamReader(System.in)));
        in.nextToken();
        int tests = (int) in.nval;
        PrintWriter out = new PrintWriter(new BufferedWriter(new OutputStreamWriter(System.out)));
        for (int t = 0; t < tests; t++) {
            in.nextToken();
            int[] p = new int[(int) in.nval];
            for (int i = 0; i < p.length; i++) {
                in.nextToken();
                p[i] = (int) in.nval;
            }
            out.println(Main.restore(p));
        }
        out.flush();
    }
}
"""


def read_line(process, timeout=5):
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        assert selector.select(timeout), "program did not flush its interactive output"
    line = process.stdout.readline()
    assert line, "program exited without completing the protocol"
    return line.rstrip("\r\n")


def interactive(classes, s, reply):
    start = time.perf_counter()
    process = subprocess.Popen(["java", "-cp", str(classes), "Main"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, bufsize=1)
    try:
        query = read_line(process)
        assert query == "? I", f"expected the one sufficient query, got {query!r}"
        process.stdin.write(str(len(reply)) + "\n")
        process.stdin.write(" ".join(map(str, reply)) + "\n")
        process.stdin.flush()
        answer = read_line(process)
        assert answer == "! " + s, (s, reply, answer)
        process.stdin.close()
        process.wait(timeout=5)
        rest = process.stdout.read()
        error = process.stderr.read()
        assert process.returncode == 0 and not rest and not error, (rest, error)
        return time.perf_counter() - start
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stdout.close()
        process.stderr.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=67067)
    parser.add_argument("--small-max", type=int, default=6)
    parser.add_argument("--random", type=int, default=2000)
    parser.add_argument("--sessions", type=int, default=24)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    # Literal fixtures catch swapped states, lost duplicate positions and a shifted final I.
    cases = [("VIVII", (1, 3, 4)), ("LXVII", (3, 4)),
             ("LXVII", (4, 4)), ("LXVII", (3, 3)),
             ("LXVII", (3, 5)), ("VIVII", (0, 3, 4))]
    owners = {}
    strings_count = 0
    exhaustive_count = 0
    for n in range(1, args.small_max + 1):
        for s in set(all_strings("67" * n)):
            strings_count += 1
            assert len(s) == 5 * n
            for reply in set(replies(s)):
                previous = owners.setdefault(reply, s)
                assert previous == s, ("ambiguous reply", previous, s, reply)
                cases.append((s, reply))
                exhaustive_count += 1

    for i in range(args.random):
        n = 1000 if i % 5 == 0 else rng.randint(1, 1000)
        s = random_string(rng, n)
        reply = list(positions(s))
        if i % 4 != 0:
            changed = rng.randrange(len(reply))
            reply[changed] += rng.choice((-1, 1))
        if i % 3 == 0:
            rng.shuffle(reply)  # The statement does not promise sorted positions.
        cases.append((s, reply))

    # Largest possible I count, errors near both boundaries, reversed input order.
    for s in ("VIVII" * 1000, "LXVII" * 1000,
              "VI" + "LXXVI" * 999 + "VII", random_string(rng, 1000)):
        original = positions(s)
        for i in (0, 1, len(original) // 2, len(original) - 2, len(original) - 1):
            for delta in (-1, 1):
                reply = list(original)
                reply[i] += delta
                cases.append((s, reply[::-1]))

    with tempfile.TemporaryDirectory(prefix="six-seven-b-") as directory:
        classes = Path(directory)
        harness = classes / "BDecoderHarness.java"
        harness.write_text(HARNESS)
        subprocess.run(["javac", "--release", "8", "-Xlint:-options", "-d", str(classes),
                        str(ROOT / "B" / "Main.java"), str(harness)], check=True)
        data = [str(len(cases))]
        for _, reply in cases:
            data.append(str(len(reply)))
            data.append(" ".join(map(str, reply)))
        start = time.perf_counter()
        result = subprocess.run(["java", "-Xmx512m", "-cp", str(classes), "BDecoderHarness"],
                                input="\n".join(data) + "\n", text=True,
                                capture_output=True, timeout=45, check=True)
        elapsed = time.perf_counter() - start
        assert not result.stderr, result.stderr
        actual = result.stdout.splitlines()
        assert len(actual) == len(cases), (len(actual), len(cases))
        for (expected, reply), got in zip(cases, actual):
            assert got == expected, ("decoder mismatch", expected, reply, got)

        protocol_cases = cases[:6] + cases[-min(args.sessions, 40):]
        times = [interactive(classes, s, reply) for s, reply in protocol_cases]
        print(f"B OK: seed={args.seed}, {strings_count} exhaustive strings, "
              f"{exhaustive_count} exhaustive replies, {args.random} random cases, "
              f"40 boundary cases; {len(cases)} decoder cases in {elapsed:.3f}s")
        print(f"B protocol OK: {len(times)} real interactive sessions, exactly one query each, "
              f"flush checked; slowest whole process {max(times):.3f}s")


if __name__ == "__main__":
    main()
