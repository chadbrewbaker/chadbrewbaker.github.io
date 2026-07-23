# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
# https://chadbrewbaker.github.io/ — companion to the 2026-07-22 union-find post
#
# Run with:  uv run php_kissat.py   (expects `kissat` on PATH or KISSAT env var)
#
# The pigeonhole principle PHP(n+1, n) is a ONE-LINE theorem semantically,
# but Haken (1985): every resolution refutation is exponential in n.
# CDCL p-simulates (and is p-simulated by) resolution, so a CDCL solver
# MUST pay the exponential price — the proof SIZE cost of the technique,
# axis 2 of the taxonomy, made physical. Watch conflicts/time blow up.

import subprocess, tempfile, time, os, re, shutil, sys

KISSAT = os.environ.get("KISSAT") or shutil.which("kissat")
if not KISSAT:
    sys.exit("kissat not found: install it (github.com/arminbiere/kissat) "
             "and put it on PATH, or set KISSAT=/path/to/kissat")

def php_cnf(holes):
    p = holes + 1                       # pigeons
    v = lambda i, j: i * holes + j + 1  # pigeon i in hole j
    cl = [[v(i, j) for j in range(holes)] for i in range(p)]          # placed
    for j in range(holes):                                            # no clash
        for i1 in range(p):
            for i2 in range(i1 + 1, p):
                cl.append([-v(i1, j), -v(i2, j)])
    return p * holes, cl

print(f"{'holes':>5} {'vars':>5} {'clauses':>7} {'result':>7} "
      f"{'conflicts':>10} {'time(s)':>8}")
for holes in range(4, 11):
    nv, cls = php_cnf(holes)
    with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False) as f:
        f.write(f"p cnf {nv} {len(cls)}\n")
        f.writelines(" ".join(map(str, c)) + " 0\n" for c in cls)
        path = f.name
    t0 = time.time()
    out = subprocess.run([KISSAT, "--time=120", path],
                         capture_output=True, text=True).stdout
    dt = time.time() - t0
    res = ("UNSAT" if "s UNSATISFIABLE" in out
           else "SAT" if "s SATISFIABLE" in out else "timeout")
    m = re.search(r"c conflicts:\s+(\d+)", out)
    conf = m.group(1) if m else "?"
    print(f"{holes:>5} {nv:>5} {len(cls):>7} {res:>7} {conf:>10} {dt:>8.2f}")
    os.unlink(path)
    if dt > 100:
        break
print("\n(One line of mathematics; exponentially long resolution proofs.")
print(" Frege proves the same statement polynomially — cost is system-relative.)")
