---
layout: post
title:  "The GPL3 Jailbreak"
date:   2020-12-10 12:50:19
categories: 
---

Remember [Reflections on Trusting Trust](https://dl.acm.org/doi/10.1145/358198.358210), Ken Thompson's compiler hack to insert back doors into operating system builds? It dawned on me that Stallman made a critical error in GPL3 - he trusted the compiler.

"The 'System Libraries' of an executable work include anything, other than the work as a whole ... or a compiler used to produce the work ... however, it does not include the work's System Libraries ..." - [ GPL V3](https://www.gnu.org/licenses/gpl-3.0.en.html).

As long as you hack the LLVM source code you aren't afoul with the GPL 3 input.
