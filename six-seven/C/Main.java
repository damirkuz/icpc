import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.IOException;

public class Main {
    private static final int DAYS = 7;
    private static final int STATES_PER_HOUSE = DAYS * DAYS;

    public static void main(String[] args) throws Exception {
        FastScanner in = new FastScanner();
        FastOutput out = new FastOutput();
        int tests = in.nextInt();
        for (int test = 0; test < tests; test++) {
            solve(in, out);
        }
        out.flush();
    }

    private static void solve(FastScanner in, FastOutput out) throws IOException {
        int n = in.nextInt();
        int[] begin = new int[n + 1];
        for (int i = 0; i < n; i++) {
            begin[i + 1] = begin[i] + (i % 2 == 0 ? 6 : 7);
        }
        int houses = begin[n];
        int[] forbidden = new int[houses];
        int[] street = new int[houses];
        int[] number = new int[houses];
        for (int i = 0; i < n; i++) {
            for (int v = begin[i]; v < begin[i + 1]; v++) {
                int value = in.nextInt();
                int mask = 0;
                while (value > 0) {
                    mask |= 1 << (value % 10 - 1);
                    value /= 10;
                }
                forbidden[v] = mask;
                street[v] = i + 1;
                number[v] = v - begin[i] + 1;
            }
        }

        int[] degree = new int[houses];
        int[] edges = new int[houses * 4];
        // i is zero-based, so these are the odd-numbered streets.
        for (int i = 0; i < n; i += 2) {
            for (int j = 0; j < 6; j++) {
                int v = begin[i] + j;
                if (i > 0) {
                    connect(v, begin[i - 1] + j, degree, edges);
                    connect(v, begin[i - 1] + j + 1, degree, edges);
                }
                if (i + 1 < n) {
                    connect(v, begin[i + 1] + j, degree, edges);
                    connect(v, begin[i + 1] + j + 1, degree, edges);
                }
            }
        }

        // State: (house * 7 + day of the next action) * 7 + returns used.
        // Days are 0..6; Monday's action is the very first action.
        int states = houses * STATES_PER_HOUSE;
        int[] parent = new int[states];
        int[] queue = new int[states];
        int head = 0;
        int tail = 1;
        parent[0] = -1;
        int finish = -1;
        while (head < tail) {
            int state = queue[head++];
            int v = state / STATES_PER_HOUSE;
            if (v == houses - 1) {
                finish = state;
                break;
            }
            int phase = state % STATES_PER_HOUSE;
            int day = phase / DAYS;
            int used = phase % DAYS;
            int nextDay = day == 6 ? 0 : day + 1;
            int dayBit = 1 << day;
            for (int edge = -1; edge < degree[v]; edge++) {
                int to = edge == -1 ? v : edges[v * 4 + edge];
                if ((forbidden[to] & dayBit) != 0) {
                    continue;
                }
                int back = street[to] < street[v] ? 1 : 0;
                if (used + back > 6) {
                    continue;
                }
                // Sunday's return is checked BEFORE the Monday reset.
                int nextUsed = day == 6 ? 0 : used + back;
                int next = (to * DAYS + nextDay) * DAYS + nextUsed;
                if (parent[next] == 0) {
                    parent[next] = state + 1;
                    queue[tail++] = next;
                }
            }
        }

        if (finish == -1) {
            out.writeInt(-67);
            out.writeByte('\n');
            return;
        }
        int length = 1;
        for (int s = finish; parent[s] != -1; s = parent[s] - 1) {
            length++;
        }
        int[] path = new int[length];
        int s = finish;
        for (int i = length - 1; i >= 0; i--) {
            path[i] = s / STATES_PER_HOUSE;
            s = parent[s] - 1;
        }
        out.writeInt(length - 1);
        out.writeByte('\n');
        for (int i = 0; i < length; i++) {
            if (i > 0) {
                out.writeByte(' ');
            }
            out.writeInt(street[path[i]]);
        }
        out.writeByte('\n');
        for (int i = 0; i < length; i++) {
            if (i > 0) {
                out.writeByte(' ');
            }
            out.writeInt(number[path[i]]);
        }
        out.writeByte('\n');
    }

    private static void connect(int a, int b, int[] degree, int[] edges) {
        edges[a * 4 + degree[a]++] = b;
        edges[b * 4 + degree[b]++] = a;
    }

    private static final class FastScanner {
        private final BufferedInputStream in = new BufferedInputStream(System.in);

        int nextInt() throws IOException {
            int c;
            do {
                c = in.read();
            } while (c <= ' ' && c != -1);
            if (c == -1) {
                return -1;
            }
            int value = 0;
            while (c > ' ') {
                value = value * 10 + c - '0';
                c = in.read();
            }
            return value;
        }
    }

    private static final class FastOutput {
        private final BufferedOutputStream out = new BufferedOutputStream(System.out);
        private final byte[] digits = new byte[10];

        void writeInt(int value) throws IOException {
            if (value < 0) {
                out.write('-');
                value = -value;
            }
            int count = 0;
            do {
                digits[count++] = (byte) ('0' + value % 10);
                value /= 10;
            } while (value > 0);
            while (count > 0) {
                out.write(digits[--count]);
            }
        }

        void writeByte(int value) throws IOException {
            out.write(value);
        }

        void flush() throws IOException {
            out.flush();
        }
    }
}
