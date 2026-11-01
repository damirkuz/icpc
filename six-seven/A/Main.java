import java.io.BufferedInputStream;
import java.io.IOException;

public class Main {
    private static final int MAX_K = 60;
    private static final long MASK = (1L << MAX_K) - 1;

    public static void main(String[] args) throws Exception {
        // On [F_n, F_(n+1)], these matrices advance by 3 * 2^(bit-1).
        long[] low = new long[MAX_K];
        long[] cross = new long[MAX_K];
        long[] high = new long[MAX_K];
        low[2] = 5;
        cross[2] = 8;
        high[2] = 13;
        for (int bit = 3; bit < MAX_K; bit++) {
            long a = low[bit - 1];
            long b = cross[bit - 1];
            long c = high[bit - 1];
            low[bit] = (a * a + b * b) & MASK;
            cross[bit] = (b * (a + c)) & MASK;
            high[bit] = (b * b + c * c) & MASK;
        }

        FastScanner input = new FastScanner();
        int q = (int) input.nextLong();
        StringBuilder answer = new StringBuilder(q * 21);
        for (int query = 0; query < q; query++) {
            int k = (int) input.nextLong();
            long x = input.nextLong();
            long n;
            long f;
            long next;
            if ((x & 3) == 3) {
                n = 1;
                f = 7;
                next = 13;
            } else {
                n = 2;
                f = 13;
                next = 20;
            }

            for (int bit = 2; bit < k; bit++) {
                if (((f ^ x) & (1L << bit)) != 0) {
                    long previousF = f;
                    // Java overflow preserves the low bits needed modulo 2^60.
                    f = (low[bit] * f + cross[bit] * next) & MASK;
                    next = (cross[bit] * previousF + high[bit] * next) & MASK;
                    n += 3L << (bit - 1);
                }
            }
            answer.append(n).append('\n');
        }
        System.out.print(answer);
    }

    private static final class FastScanner {
        private final BufferedInputStream input = new BufferedInputStream(System.in);

        long nextLong() throws IOException {
            int c;
            do {
                c = input.read();
            } while (c <= ' ' && c != -1);
            long value = 0;
            while (c > ' ') {
                value = value * 10 + c - '0';
                c = input.read();
            }
            return value;
        }
    }
}
