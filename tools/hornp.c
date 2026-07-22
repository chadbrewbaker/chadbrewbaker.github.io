// horn.c — freestanding Datalog / Horn-clause engine for wasm32.
// Semi-naive bottom-up fixpoint. No libc. All strings interned by the host;
// the engine sees only u32 symbols and i32 terms (>=0 constant, <0 variable -1-v).
typedef unsigned int u32;
typedef int i32;
typedef unsigned long usize;

#define EXPORT(name) __attribute__((export_name(#name)))

extern unsigned char __heap_base;
static usize heap_top = 0;
static usize heap_end = 0;

static void *bump(usize n) {
  n = (n + 7u) & ~7u;
  if (heap_top == 0) {
    heap_top = (usize)&__heap_base;
    heap_end = (usize)(__builtin_wasm_memory_size(0) * 65536u);
  }
  if (heap_top + n > heap_end) {
    usize need = (heap_top + n - heap_end + 65535u) / 65536u;
    usize extra = need < 64 ? 64 : need;          // grow in >=4MB steps
    if (__builtin_wasm_memory_grow(0, extra) == (usize)-1) {
      if (__builtin_wasm_memory_grow(0, need) == (usize)-1) return 0;
      heap_end += need * 65536u;
    } else heap_end += extra * 65536u;
  }
  void *p = (void *)heap_top;
  heap_top += n;
  return p;
}

void *memset(void *d, int c, usize n) {           // clang may synthesize calls
  unsigned char *p = d;
  while (n--) *p++ = (unsigned char)c;
  return d;
}
void *memcpy(void *d, const void *s, usize n) {
  unsigned char *p = d; const unsigned char *q = s;
  while (n--) *p++ = *q++;
  return d;
}

// ---------------- relations ----------------
#define MAXPRED 512
#define MAXARITY 8
typedef struct { u32 *slots; u32 cap; u32 n; } ColMap;  // slots: pairs (value, head)
typedef struct {
  u32 arity;
  u32 *data;        // count * arity u32s
  u32 count, cap;
  u32 *index;       // open-addressing: slot -> tuple_id+1, 0 empty
  u32 icap;         // power of two
  u32 delta_lo, delta_hi;   // [lo,hi) = delta of previous round
  u32 present0;     // arity-0 flag
  ColMap col[MAXARITY];     // per-column value -> chain head (tuple_id+1)
  u32 *next[MAXARITY];      // chain next per tuple (tuple_id+1 or 0)
  u32 *prov_rule;   // per tuple: rule id (0xFFFFFFFF = asserted fact)
  u32 *prov_off;    // per tuple: offset into prov_arena (pairs pred,idx)
  u32 *prov_n;      // per tuple: number of premises
  u32 prov_cap;
} Rel;

static u32 *prov_arena = 0;
static u32 prov_len = 0, prov_capa = 0;
static u32 prov_push(const u32 *pairs, u32 n) {
  if (prov_len + 2 * n > prov_capa) {
    u32 ncap = prov_capa ? prov_capa * 2 : 4096;
    while (ncap < prov_len + 2 * n) ncap *= 2;
    u32 *na = bump((usize)ncap * 4u);
    memcpy(na, prov_arena, (usize)prov_len * 4u);
    prov_arena = na; prov_capa = ncap;
  }
  u32 off = prov_len;
  memcpy(prov_arena + prov_len, pairs, (usize)n * 8u);
  prov_len += 2 * n;
  return off;
}
static void prov_ensure(Rel *r, u32 need) {
  if (need <= r->prov_cap) return;
  u32 ncap = r->prov_cap ? r->prov_cap * 2 : 64;
  while (ncap < need) ncap *= 2;
  u32 *a = bump((usize)ncap * 4u), *b = bump((usize)ncap * 4u), *c = bump((usize)ncap * 4u);
  if (r->prov_cap) {
    memcpy(a, r->prov_rule, (usize)r->prov_cap * 4u);
    memcpy(b, r->prov_off,  (usize)r->prov_cap * 4u);
    memcpy(c, r->prov_n,    (usize)r->prov_cap * 4u);
  }
  r->prov_rule = a; r->prov_off = b; r->prov_n = c; r->prov_cap = ncap;
}

static u32 colmap_slot(ColMap *m, u32 value) {   // find or create slot index
  u32 mask = m->cap - 1;
  u32 h = (value * 2654435761u) & mask;
  while (m->slots[2 * h] != 0xFFFFFFFFu) {
    if (m->slots[2 * h] == value) return h;
    h = (h + 1) & mask;
  }
  return h;
}
static void colmap_grow(ColMap *m) {
  u32 ncap = m->cap * 2;
  u32 *ns = bump((usize)ncap * 8u);
  for (u32 i = 0; i < ncap * 2; i += 2) { ns[i] = 0xFFFFFFFFu; ns[i + 1] = 0; }
  u32 *os = m->slots; u32 ocap = m->cap;
  m->slots = ns; m->cap = ncap;
  for (u32 i = 0; i < ocap; i++)
    if (os[2 * i] != 0xFFFFFFFFu) {
      u32 h = colmap_slot(m, os[2 * i]);
      m->slots[2 * h] = os[2 * i]; m->slots[2 * h + 1] = os[2 * i + 1];
    }
}

static Rel rels[MAXPRED];
static u32 nrels = 0;

static u32 hash_tuple(const u32 *t, u32 arity) {
  u32 h = 2166136261u;
  for (u32 i = 0; i < arity; i++) { h ^= t[i]; h *= 16777619u; }
  return h ? h : 1u;
}

static void reindex(Rel *r, u32 icap) {
  u32 *idx = bump(icap * 4u);
  memset(idx, 0, icap * 4u);
  for (u32 t = 0; t < r->count; t++) {
    u32 h = hash_tuple(r->data + (usize)t * r->arity, r->arity) & (icap - 1);
    while (idx[h]) h = (h + 1) & (icap - 1);
    idx[h] = t + 1;
  }
  r->index = idx; r->icap = icap;
}

EXPORT(dl_reset) void dl_reset(void) {
  heap_top = (usize)&__heap_base;                  // arena discard
  heap_end = (usize)(__builtin_wasm_memory_size(0) * 65536u);
  nrels = 0;
  memset(rels, 0, sizeof rels);
  prov_arena = 0; prov_len = 0; prov_capa = 0;
}

EXPORT(dl_add_pred) i32 dl_add_pred(u32 arity) {
  if (nrels >= MAXPRED) return -1;
  Rel *r = &rels[nrels];
  r->arity = arity;
  r->count = 0; r->cap = 0; r->data = 0;
  r->icap = 64; r->index = bump(64 * 4u); memset(r->index, 0, 64 * 4u);
  r->delta_lo = r->delta_hi = 0; r->present0 = 0;
  if (arity > MAXARITY) return -2;
  for (u32 c = 0; c < arity; c++) {
    r->col[c].cap = 64; r->col[c].n = 0;
    r->col[c].slots = bump(64 * 8u);
    for (u32 i = 0; i < 128; i += 2) { r->col[c].slots[i] = 0xFFFFFFFFu; r->col[c].slots[i + 1] = 0; }
    r->next[c] = 0;
  }
  return (i32)nrels++;
}

// returns 1 if tuple was new
static u32 insert(Rel *r, const u32 *t, u32 rule, const u32 *prem, u32 nprem) {
  if (r->arity == 0) {
    if (r->present0) return 0;
    r->present0 = 1; r->count = 1;
    prov_ensure(r, 1);
    r->prov_rule[0] = rule; r->prov_n[0] = nprem;
    r->prov_off[0] = nprem ? prov_push(prem, nprem) : 0;
    return 1;
  }
  u32 mask = r->icap - 1;
  u32 h = hash_tuple(t, r->arity) & mask;
  while (r->index[h]) {
    u32 id = r->index[h] - 1;
    const u32 *u = r->data + (usize)id * r->arity;
    u32 same = 1;
    for (u32 i = 0; i < r->arity; i++) if (u[i] != t[i]) { same = 0; break; }
    if (same) return 0;
    h = (h + 1) & mask;
  }
  if (r->count == r->cap) {
    u32 ncap = r->cap ? r->cap * 2 : 64;
    u32 *nd = bump((usize)ncap * r->arity * 4u);
    if (r->count) memcpy(nd, r->data, (usize)r->count * r->arity * 4u);
    r->data = nd; r->cap = ncap;
    for (u32 c = 0; c < r->arity; c++) {
      u32 *nn = bump((usize)ncap * 4u);
      if (r->count) memcpy(nn, r->next[c], (usize)r->count * 4u);
      r->next[c] = nn;
    }
  }
  memcpy(r->data + (usize)r->count * r->arity, t, r->arity * 4u);
  u32 id = r->count;
  prov_ensure(r, id + 1);
  r->prov_rule[id] = rule; r->prov_n[id] = nprem;
  r->prov_off[id] = nprem ? prov_push(prem, nprem) : 0;
  r->index[h] = ++r->count;
  for (u32 c = 0; c < r->arity; c++) {
    ColMap *m = &r->col[c];
    if (m->n * 4u >= m->cap * 3u) colmap_grow(m);
    u32 s = colmap_slot(m, t[c]);
    if (m->slots[2 * s] == 0xFFFFFFFFu) { m->slots[2 * s] = t[c]; m->slots[2 * s + 1] = 0; m->n++; }
    r->next[c][id] = m->slots[2 * s + 1];
    m->slots[2 * s + 1] = id + 1;
  }
  if (r->count * 4u >= r->icap * 3u) reindex(r, r->icap * 2);
  return 1;
}

static u32 scratch_buf[64];
EXPORT(dl_scratch) u32 *dl_scratch(void) { return scratch_buf; }

EXPORT(dl_fact) i32 dl_fact(u32 pred) {
  if (pred >= nrels) return -1;
  return (i32)insert(&rels[pred], scratch_buf, 0xFFFFFFFFu, 0, 0);
}

// ---------------- rules ----------------
// blob (i32 stream): nrules, then per rule:
//   nvars, headPred, nbody, head terms (arity of headPred),
//   then per body atom: pred, terms (arity of pred)
static i32 *rules_blob = 0;
static u32 rules_len = 0;

EXPORT(dl_alloc) u32 dl_alloc(u32 n) { return (u32)(usize)bump(n); }
EXPORT(dl_set_rules) void dl_set_rules(u32 ptr, u32 len) {
  rules_blob = (i32 *)(usize)ptr; rules_len = len;
}

#define MAXVARS 64
#define MAXBODY 32

typedef struct { u32 pred; const i32 *terms; } Atom;

static i32 env[MAXVARS];

// match tuple against atom terms under env; record newly bound vars in undo
static u32 match(const Atom *a, const u32 *tuple, u32 arity, i32 *undo, u32 *nundo) {
  for (u32 i = 0; i < arity; i++) {
    i32 t = a->terms[i];
    if (t >= 0) { if ((u32)t != tuple[i]) goto fail; }
    else {
      u32 v = (u32)(-1 - t);
      if (env[v] >= 0) { if ((u32)env[v] != tuple[i]) goto fail; }
      else { env[v] = (i32)tuple[i]; undo[(*nundo)++] = (i32)v; }
    }
  }
  return 1;
fail:
  return 0;
}

static u32 new_this_round;

static u32 join_order[MAXBODY];
static u32 cur_idx[MAXBODY];
static u32 cur_rule = 0xFFFFFFFFu;

// recursive join over atoms in join_order; slot 0 is the delta atom
static void join(const Atom *atoms, u32 nbody, u32 pos, u32 di,
                 u32 headPred, const i32 *headTerms) {
  if (pos == nbody) {
    Rel *hr = &rels[headPred];
    u32 t[32];
    for (u32 i = 0; i < hr->arity; i++) {
      i32 x = headTerms[i];
      t[i] = x >= 0 ? (u32)x : (u32)env[-1 - x];
    }
    u32 prem[2 * MAXBODY];
    for (u32 ai = 0; ai < nbody; ai++) {
      prem[2 * ai] = atoms[ai].pred;
      prem[2 * ai + 1] = cur_idx[ai];
    }
    new_this_round += insert(hr, t, cur_rule, prem, nbody);
    return;
  }
  u32 ai = join_order[pos];
  const Atom *a = &atoms[ai];
  Rel *r = &rels[a->pred];
  u32 is_delta = (ai == di);
  u32 lo = is_delta ? r->delta_lo : 0;
  u32 hi = is_delta ? r->delta_hi : r->count;
  if (r->arity == 0) {
    if (is_delta ? (r->delta_lo < r->delta_hi) : r->present0) {
      cur_idx[ai] = 0;
      join(atoms, nbody, pos + 1, di, headPred, headTerms);
    }
    return;
  }
  i32 undo[32];
  // find a bound column for indexed lookup
  for (u32 c = 0; c < r->arity; c++) {
    i32 t = a->terms[c];
    u32 bound = 0, val = 0;
    if (t >= 0) { bound = 1; val = (u32)t; }
    else if (env[-1 - t] >= 0) { bound = 1; val = (u32)env[-1 - t]; }
    if (!bound) continue;
    ColMap *m = &r->col[c];
    u32 s = colmap_slot(m, val);
    if (m->slots[2 * s] == 0xFFFFFFFFu) return;      // value absent -> no matches
    for (u32 id1 = m->slots[2 * s + 1]; id1; id1 = r->next[c][id1 - 1]) {
      u32 id = id1 - 1;
      if (id < lo || id >= hi) continue;
      u32 nundo = 0;
      if (match(a, r->data + (usize)id * r->arity, r->arity, undo, &nundo)) {
        cur_idx[ai] = id;
        join(atoms, nbody, pos + 1, di, headPred, headTerms);
      }
      for (u32 i = 0; i < nundo; i++) env[undo[i]] = -1;
    }
    return;
  }
  for (u32 t = lo; t < hi; t++) {
    u32 nundo = 0;
    if (match(a, r->data + (usize)t * r->arity, r->arity, undo, &nundo)) {
      cur_idx[ai] = t;
      join(atoms, nbody, pos + 1, di, headPred, headTerms);
    }
    for (u32 i = 0; i < nundo; i++) env[undo[i]] = -1;
  }
}

EXPORT(dl_run) u32 dl_run(u32 max_rounds) {
  // round 0: everything currently stored is the first delta
  for (u32 p = 0; p < nrels; p++) {
    rels[p].delta_lo = 0;
    rels[p].delta_hi = rels[p].count;
  }
  u32 rounds = 0;
  while (rounds < max_rounds) {
    u32 mark[MAXPRED];
    for (u32 p = 0; p < nrels; p++) mark[p] = rels[p].count;
    new_this_round = 0;
    const i32 *b = rules_blob;
    u32 nr = (u32)*b++;
    for (u32 ri = 0; ri < nr; ri++) {
      cur_rule = ri;
      u32 nvars = (u32)*b++;
      u32 headPred = (u32)*b++;
      u32 nbody = (u32)*b++;
      const i32 *headTerms = b; b += rels[headPred].arity;
      Atom atoms[MAXBODY];
      for (u32 ai = 0; ai < nbody; ai++) {
        atoms[ai].pred = (u32)*b++;
        atoms[ai].terms = b; b += rels[atoms[ai].pred].arity;
      }
      for (u32 v = 0; v < nvars; v++) env[v] = -1;
      if (nbody == 0) {                    // rule with empty body = fact
        join(atoms, 0, 0, 0, headPred, headTerms);
        continue;
      }
      for (u32 di = 0; di < nbody; di++) {
        Rel *dr = &rels[atoms[di].pred];
        if (dr->delta_lo >= dr->delta_hi && !(dr->arity == 0 && rounds == 0)) continue;
        join_order[0] = di;
        for (u32 k = 0, w = 1; k < nbody; k++) if (k != di) join_order[w++] = k;
        join(atoms, nbody, 0, di, headPred, headTerms);
      }
    }
    rounds++;
    for (u32 p = 0; p < nrels; p++) {
      rels[p].delta_lo = mark[p];
      rels[p].delta_hi = rels[p].count;
    }
    if (!new_this_round) break;
  }
  return rounds;
}

EXPORT(dl_count) u32 dl_count(u32 pred) { return pred < nrels ? rels[pred].count : 0; }
EXPORT(dl_arity) u32 dl_arity(u32 pred) { return pred < nrels ? rels[pred].arity : 0; }
EXPORT(dl_tuples) u32 dl_tuples(u32 pred) { return (u32)(usize)rels[pred].data; }
EXPORT(dl_prov_rule) u32 dl_prov_rule(u32 pred, u32 t) { return rels[pred].prov_rule[t]; }
EXPORT(dl_prov_n)    u32 dl_prov_n(u32 pred, u32 t)    { return rels[pred].prov_n[t]; }
EXPORT(dl_prov_prem_pred) u32 dl_prov_prem_pred(u32 pred, u32 t, u32 i) {
  return prov_arena[rels[pred].prov_off[t] + 2 * i];
}
EXPORT(dl_prov_prem_idx) u32 dl_prov_prem_idx(u32 pred, u32 t, u32 i) {
  return prov_arena[rels[pred].prov_off[t] + 2 * i + 1];
}
EXPORT(dl_total) u32 dl_total(void) {
  u32 s = 0;
  for (u32 p = 0; p < nrels; p++) s += rels[p].count;
  return s;
}
