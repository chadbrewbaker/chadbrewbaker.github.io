---
layout: post
title:  "Faster Clang"
date:   2018-06-20 12:38:19
categories: C, Clang
---
Sticky notes on speeding up Clang builds and rebuilds. Expect a lot of edits.


The first issue is that Makefiles generated by CMake don't always incldue header information. Not to mention C++ can recursively add in headers.

```bash
clang++ -H hello.cpp
```

That will list all the headers.


I couldn't get http://thothonegan.tumblr.com/post/154694339433/profiling-a-cmake-build to work. First you have to use gtime under OSX and sed needs different flags

```bash
sed -i 'something' #Linux
sed -i -e 'something' #OSX
```

Here is what I ended up using, call this file rusage\_cpp.
```bash
exec gtime -f '%e (elapsed)   rc=%x elapsed=%e user=%U system=%S maxrss=%M avgrss=%t ins=%I outs=%O minflt=%R majflt=%F swaps=%W avgmem=%K avgdata=%D argv="%C"' clang++ -H   "$@"
```

```bash
cmake .. -DCMAKE_CXX_COMPILER=/usr/bin/rusage_cpp 
```

Next what about those headers? Clang supports precompiling them https://clang.llvm.org/docs/PCHInternals.html

Next, some sort of caching of objecy files

* How much faster is clang if you throw it all the things to compile at once instead of one object at a time?

* How cache oblivious are Clang's string data structures?

* 


