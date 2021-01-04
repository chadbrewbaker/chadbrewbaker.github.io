---
layout: post
title:  "Godbolting the Benchmarks Game"
date:   2021-01-03 12:50:19
categories: 
---

[Lobste.rs reported](https://lobste.rs/s/breqgw/rust_is_now_overall_faster_than_c) that Rust is now faster than C across the board. Why? Lack of a good standard library and cache alignment were my gut feelings.

First off, many of these codes don't Godbolt due to crates. You would have to [expand](https://github.com/dtolnay/cargo-expand) the Rust.

On the command line:

```bash
cargo rustc —-profile=check -- -Zunstable-options --pretty=expanded
```

But that only expands macros in local code, you still don't get crate code expansion.

```bash
cargo install cargo-xbuild
rustup component add rust-src
```

This lets you get llvm-ir down to core libraries via setting up for cross-compilation, but it wasn't working for me on aarch64 MacOS.

The [play.rust-lang](https://play.rust-lang.org) did work but the output was *huge*. It emits [miri](https://github.com/rust-lang/miri), llvm-ir, and x86_64. The source is [here](https://github.com/integer32llc/rust-playground).

I think I will circle back after thinking about how to automate the comparison at the LLVM IR level. First many of the codes are using different algorithms, and more importantly different memory allocation/access patterns. To bring C up to C++/Rust performance using allocation pools etc seems critical. I also want to know the performance bump of profile guided optimization - and how those branch predicions can be baked in.
