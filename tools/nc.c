// nc.c — sequential baselines (the serial fraction) for the NC demo page.
// Freestanding wasm32, no libc. u32 math throughout, exact mod 2^32,
// matching the bsd-tier WGSL kernels (see amdahl gpu/wgsl/*.wgsl).
typedef unsigned int u32;
typedef unsigned long usize;
#define EXPORT(name) __attribute__((export_name(#name)))

extern unsigned char __heap_base;
static usize top = 0, end_ = 0;
static void *bump(usize n) {
  n = (n + 7u) & ~7u;
  if (!top) { top = (usize)&__heap_base; end_ = __builtin_wasm_memory_size(0) * 65536u; }
  while (top + n > end_) {
    if (__builtin_wasm_memory_grow(0, 64) == (usize)-1) return 0;
    end_ += 64 * 65536u;
  }
  void *p = (void *)top; top += n; return p;
}
void *memcpy(void *d, const void *s, usize n) {
  unsigned char *p = d; const unsigned char *q = s;
  while (n--) *p++ = *q++;
  return d;
}
void *memset(void *d, int c, usize n) {
  unsigned char *p = d; while (n--) *p++ = (unsigned char)c; return d;
}
EXPORT(nc_reset) void nc_reset(void) { top = (usize)&__heap_base; }
EXPORT(nc_alloc) u32 nc_alloc(u32 n) { return (u32)(usize)bump(n); }

// inclusive prefix sums in place — the tuned serial loop (one pass)
EXPORT(seq_scan) void seq_scan(u32 *a, u32 n) {
  u32 s = 0;
  for (u32 i = 0; i < n; i++) { s += a[i]; a[i] = s; }
}

// LSD radix sort, 4x8-bit passes — an honest fast serial u32 sort baseline
EXPORT(seq_sort) void seq_sort(u32 *a, u32 n) {
  u32 *tmp = bump((usize)n * 4u);
  for (u32 shift = 0; shift < 32; shift += 8) {
    u32 cnt[257];
    memset(cnt, 0, sizeof cnt);
    for (u32 i = 0; i < n; i++) cnt[((a[i] >> shift) & 255u) + 1]++;
    for (u32 i = 0; i < 256; i++) cnt[i + 1] += cnt[i];
    for (u32 i = 0; i < n; i++) tmp[cnt[(a[i] >> shift) & 255u]++] = a[i];
    u32 *t = a; a = tmp; tmp = t;
  }
  // 4 passes = even count: result already back in the original buffer
}

// list ranking, sequential: walk from the head, assign distance-to-tail
// succ[tail] == tail. rank output buffer supplied by host.
EXPORT(seq_listrank) u32 seq_listrank(const u32 *succ, u32 *rank, u32 n) {
  unsigned char *pointed = bump(n);
  memset(pointed, 0, n);
  for (u32 i = 0; i < n; i++) if (succ[i] != i) pointed[succ[i]] = 1;
  u32 head = 0;
  for (u32 i = 0; i < n; i++) if (!pointed[i]) { head = i; break; }
  // first walk: find length
  u32 len = 1, v = head;
  while (succ[v] != v) { v = succ[v]; len++; }
  // second walk: distance to tail = len-1-pos
  v = head;
  for (u32 pos = 0; pos < len; pos++) { rank[v] = len - 1 - pos; v = succ[v]; }
  return len;
}

// dense matmul C = A*B mod 2^32, i-k-j loop order (cache-friendly serial baseline)
EXPORT(seq_matmul) void seq_matmul(const u32 *A, const u32 *B, u32 *C, u32 n) {
  for (u32 i = 0; i < n; i++) {
    for (u32 j = 0; j < n; j++) C[i * n + j] = 0;
    for (u32 k = 0; k < n; k++) {
      u32 a = A[i * n + k];
      const u32 *brow = B + (usize)k * n;
      u32 *crow = C + (usize)i * n;
      for (u32 j = 0; j < n; j++) crow[j] += a * brow[j];
    }
  }
}

// Horn unit resolution (Dowling–Gallier): the P-complete counterpoint.
// blob: nclauses, then per clause: head, nbody, body...
// atoms are 0..natoms-1. Returns number of true atoms at the fixpoint.
EXPORT(horn_solve) u32 horn_solve(const u32 *blob, u32 natoms) {
  u32 nclauses = *blob++;
  const u32 *cl = blob;
  // index: for each atom, list of clauses whose body contains it
  u32 *deg = bump((usize)natoms * 4u); memset(deg, 0, (usize)natoms * 4u);
  u32 *heads = bump((usize)nclauses * 4u);
  u32 *need = bump((usize)nclauses * 4u);
  const u32 *p = cl;
  u32 total_occ = 0;
  for (u32 c = 0; c < nclauses; c++) {
    heads[c] = *p++;
    u32 nb = *p++; need[c] = nb; total_occ += nb;
    for (u32 j = 0; j < nb; j++) deg[*p++]++;
  }
  u32 *start = bump((usize)(natoms + 1) * 4u);
  start[0] = 0;
  for (u32 a = 0; a < natoms; a++) start[a + 1] = start[a] + deg[a];
  u32 *occ = bump((usize)total_occ * 4u);
  u32 *fill = bump((usize)natoms * 4u); memset(fill, 0, (usize)natoms * 4u);
  p = cl;
  for (u32 c = 0; c < nclauses; c++) {
    p++; u32 nb = *p++;
    for (u32 j = 0; j < nb; j++) { u32 a = *p++; occ[start[a] + fill[a]++] = c; }
  }
  unsigned char *truth = bump(natoms); memset(truth, 0, natoms);
  u32 *queue = bump((usize)natoms * 4u);
  u32 qh = 0, qt = 0, ntrue = 0;
  for (u32 c = 0; c < nclauses; c++)
    if (need[c] == 0 && !truth[heads[c]]) { truth[heads[c]] = 1; queue[qt++] = heads[c]; ntrue++; }
  while (qh < qt) {
    u32 a = queue[qh++];
    for (u32 k = start[a]; k < start[a + 1]; k++) {
      u32 c = occ[k];
      if (--need[c] == 0 && !truth[heads[c]]) {
        truth[heads[c]] = 1; queue[qt++] = heads[c]; ntrue++;
      }
    }
  }
  return ntrue;
}
