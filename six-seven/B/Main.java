import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Arrays;

public class Main {
    // States: next decimal digit is 6; next digit is 7; one more I is required.
    private static final int[][] NEXT = {
        {-1, -1, 1, -1, 2, -1, -1, 1},
        {-1, -1, 2, -1, -1, 1, -1, 2},
        {-1, 0, -1, -1, -1, -1, -1, -1}
    };
    private static final String[][] TEXT = {
        {null, null, "VI", null, "LXVI", null, null, "DCLXXVI"},
        {null, null, "VI", null, null, "LXXVI", null, "DCCLXVI"},
        {null, "I", null, null, null, null, null, null}
    };

    private static int step(int state, int gap) {
        if (state < 0 || gap < 0 || gap >= 8) {
            return -1;
        }
        return NEXT[state][gap];
    }

    static String restore(int[] positions) {
        Arrays.sort(positions);
        int m = positions.length;
        if (m == 0) {
            throw new IllegalArgumentException("A valid string contains I");
        }
        int[] gaps = new int[m];
        for (int i = 0; i < m; i++) {
            gaps[i] = positions[i] - (i == 0 ? -1 : positions[i - 1]);
        }

        int[] prefix = new int[m + 1];
        for (int i = 0; i < m; i++) {
            prefix[i + 1] = step(prefix[i], gaps[i]);
        }
        if (prefix[m] == 0) {
            return render(gaps);
        }

        // suffix[state][i]: gaps i..m-1 complete a valid string from state.
        boolean[][] suffix = new boolean[3][m + 1];
        suffix[0][m] = true;
        for (int i = m - 1; i >= 0; i--) {
            for (int state = 0; state < 3; state++) {
                int next = step(state, gaps[i]);
                suffix[state][i] = next >= 0 && suffix[next][i + 1];
            }
        }

        for (int i = 0; i < m; i++) {
            for (int delta = -1; delta <= 1; delta += 2) {
                // Moving one position changes only its two neighboring gaps.
                int next = step(prefix[i], gaps[i] + delta);
                int suffixStart = i + 1;
                if (suffixStart < m) {
                    next = step(next, gaps[suffixStart] - delta);
                    suffixStart++;
                }
                if (next >= 0 && suffix[next][suffixStart]) {
                    gaps[i] += delta;
                    if (i + 1 < m) {
                        gaps[i + 1] -= delta;
                    }
                    return render(gaps);
                }
            }
        }
        throw new IllegalArgumentException("Reply is inconsistent with the statement");
    }

    private static String render(int[] gaps) {
        StringBuilder answer = new StringBuilder();
        int state = 0;
        for (int gap : gaps) {
            answer.append(TEXT[state][gap]);
            state = NEXT[state][gap];
        }
        return answer.toString();
    }

    public static void main(String[] args) throws Exception {
        PrintWriter out = new PrintWriter(System.out);
        out.println("? I");
        out.flush();

        FastInput in = new FastInput();
        int count = in.nextInt();
        if (count < 0) {
            return;
        }
        int[] positions = new int[count];
        for (int i = 0; i < count; i++) {
            positions[i] = in.nextInt();
        }
        out.println("! " + restore(positions));
        out.flush();
    }

    private static final class FastInput {
        private final BufferedInputStream in = new BufferedInputStream(System.in);

        int nextInt() throws IOException {
            int c;
            do {
                c = in.read();
            } while (c >= 0 && c <= ' ');
            if (c < 0) {
                return -1;
            }
            int sign = 1;
            if (c == '-') {
                sign = -1;
                c = in.read();
            }
            int value = 0;
            while (c >= '0' && c <= '9') {
                value = value * 10 + c - '0';
                c = in.read();
            }
            return value * sign;
        }
    }
}
