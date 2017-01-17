---
layout: post
title:  "The state of C/C++ tools 0 of N"
date:   2016-12-14 12:38:19
categories: Developer Automation, C, C++, Clang, LLVM, GCC
---

I have a client with a very interesting C++ project porting an amazing tool to Android. It has went from debugging memory leaks induced by Swig in JNI bindings cleaning up the codebase so it is a solid Android native library.


```bash
cmake; autoconf
clang; scan-build
clang; gcov
bear; oclint
valgrind
clang -fsanitize=address
afl; libFuzzer
klee
souper
c2hs
clang -M ; cmake --graphviz #  Dependency analysis tools.
#LLVM code coverage, need to figure out how
whole-program-llvm
gprof; criterion
clang-format # Passes to automatically make code more human readable or safer at the AST level.
```

Esentially the entire modern toolchain of just getting the darn thing to build, static compiler warnings, dynamic code coverage, dynaic memory leak checking, benchmarking to identify slow stuff, brute fuzzing (string logic is hard), extending the linker with expressive type information, and concolic methods to automatically generate unit tests with SMT solvers.


First article will probably deal with make, cmake, and autotools.  How to get CC, CXX, CFLAGS, CPPFLAGS, LD, LDFLAGS propigated so we can wire up the compiler how we want it and tell the compiler which system includes and libraries to use.

Clang/LLVM now have numerious incompatible code coverage methods which is an article unto itself.

oclint and clang-format will focus on how to write your own AST transforms.

Most likely an article covering c2hs and how Haskell uses ".hi" files to extend object file type information. 

