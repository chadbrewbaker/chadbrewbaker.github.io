// listrank.wgsl — Wyllie pointer jumping, WebGPU/WGSL (bsd tier).
// Provenance: [JáJá92] Sec. 2.2 / 3.1; mirrors bsd/nc/listrank.py:
// rank'[i] = rank[i] + rank[next[i]]; next'[i] = next[next[i]].
// T = O(log n), W = O(n log n) — Wyllie, deliberately not work-optimal
// (same note as listrank.py; the point here is the round count).
// The host issues ceil(log2 n) dispatches, ping-ponging (rank,next)
// buffers between bind groups — the round IS the dispatch, no grid-wide
// barrier exists inside one (the package's standing model, cf. scan.wgsl).
// succ[tail] == tail keeps rank[tail] = 0 through every round.

@group(0) @binding(0) var<storage, read>       rank_in:  array<u32>;
@group(0) @binding(1) var<storage, read>       next_in:  array<u32>;
@group(0) @binding(2) var<storage, read_write> rank_out: array<u32>;
@group(0) @binding(3) var<storage, read_write> next_out: array<u32>;

@compute @workgroup_size(256)
fn jump(@builtin(global_invocation_id) gid: vec3<u32>) {
    let i = gid.x;
    if (i >= arrayLength(&rank_in)) { return; }
    let nx = next_in[i];
    rank_out[i] = rank_in[i] + rank_in[nx];
    next_out[i] = next_in[nx];
}
