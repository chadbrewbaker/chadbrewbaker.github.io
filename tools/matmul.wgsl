// matmul.wgsl — dense C = A*B as an explicit NC circuit, WebGPU/WGSL
// (bsd tier). Provenance: [JáJá92] ch. 8 (matrix ops on the PRAM).
// T = O(log n), W = O(n^3): dispatch 1 ("mul") materializes all n^3
// products prod[(i*n+j)*n + k] = A[i][k]*B[k][j]; then log2(n) "reduce"
// dispatches halve the k-extent by pairwise sums — the binary reduction
// tree of the depth-O(log n) circuit, one tree level per kernel launch
// (the round IS the dispatch, cf. scan.wgsl). C[i][j] ends in
// prod[(i*n+j)*n + 0]. u32 mod 2^32 exactly, matching seq_matmul in nc.c.
// The k-major product layout keeps each reduce round's reads coalesced.
// Capacity: n^3 u32s must fit one storage buffer (n=256 -> 64 MiB).

struct Params { n: u32, s: u32, pad0: u32, pad1: u32 };

@group(0) @binding(0) var<storage, read>       A: array<u32>;
@group(0) @binding(1) var<storage, read>       B: array<u32>;
@group(0) @binding(2) var<storage, read_write> prod: array<u32>;
@group(0) @binding(3) var<uniform> p: Params;

// Dispatches are 2D: total threads can exceed 65535*256 in one dimension
// (n=256 needs 65536 groups — one past maxComputeWorkgroupsPerDimension,
// caught on llvmpipe). Linear id = gid.x + gid.y * groups_x * 256.
@compute @workgroup_size(256)
fn mul(@builtin(global_invocation_id) gid: vec3<u32>,
       @builtin(num_workgroups) nwg: vec3<u32>) {
    let t = gid.x + gid.y * nwg.x * 256u;
    let n = p.n;
    if (t >= n * n * n) { return; }
    let k = t % n;
    let ij = t / n;
    let i = ij / n;
    let j = ij % n;
    prod[t] = A[i * n + k] * B[k * n + j];
}

@compute @workgroup_size(256)
fn reduce(@builtin(global_invocation_id) gid: vec3<u32>,
          @builtin(num_workgroups) nwg: vec3<u32>) {
    let t = gid.x + gid.y * nwg.x * 256u;
    let n = p.n;
    let s = p.s;
    if (t >= n * n * s) { return; }
    let k = t % s;
    let ij = t / s;
    let base = ij * n + k;
    // in-row guard: without it, base+s crosses into the next (i,j) cell's
    // k-range whenever k+s >= n (non-power-of-2 n) — caught on llvmpipe.
    if (k + s < n) {
        prod[base] = prod[base] + prod[base + s];
    }
}
