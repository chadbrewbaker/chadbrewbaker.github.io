---
layout: post
title:  "Compositional Equality"
date:   2014-07-28 14:05:00
categories: combinatorics transformations permutations equivalence
---

In studying transformation composition I ran into a lot of sequences not in OEIS. I will list them here. Big thanks to Alois Heinz and Giovanni Resta  for providing extra terms, and Neil Slone for expediting their publication. Also thanks to Alexander Burstein for helping me factor them into Wilf equivalence classes.

Over the next decade I hope we get a lot more of what I call Concrete Algebra, using concrete examples of permutations and transformations to constructively rebuild Algebra and functional programming from the ground up. Cayley and Yoneda showed us we could do this.  Groups, Rings, Fields, QuasiGroups, Loops, SemiRings, NearSemiRings, .... these are the ones we study. How about 99% of the structures we haven't bothered to look at yet, let alone name?

Algebra is Arabic for "reunion of broken parts". Lets build something.

##Over all transformations (endofunctions)
[f(g(f(x))) = f(f(f(x)))](https://oeis.org/A239773)

[f(g(f(x))) = g(g(f(x)))](https://oeis.org/A239769)

[f(f(x)) = g(f(g(x)))](https://oeis.org/A239749)

[f(x) = g(g(f(x)))](https://oeis.org/A239771)

[f(x) = g(f(f(x)))](https://oeis.org/A235328)

[g(f(x)) = f(f(f(x)))](https://oeis.org/A239750)

[f(g(x)) = f(x)](https://oeis.org/A239761)

[f(f(x)) = g(g(g(x)))](https://oeis.org/A235325)

[f(f(f(x))) = g(g(g(x)))](https://oeis.org/A235326)

[f(f(x)) = g(g(x))](https://oeis.org/A235327)

[f(f(x)) = g(f(f(x))](https://oeis.org/A239752)

[f(x) = g(f(g(x))](https://oeis.org/A239753)

[f(g(f(x))) = g(g(g(x)))](https://oeis.org/A239754)

[f(g(x)) = g(f(f(x)))](https://oeis.org/A239755)

[f(g(g(x))) = g(f(f(x)))](https://oeis.org/A239757)

[f(g(f(x))) = g(f(g(x)))](https://oeis.org/A239758)

[f(x) = f(f(g(x)))](https://oeis.org/A239760)

[f(f(g(x))) = g(f(x))](https://oeis.org/A239762)

[f(f(x)) = f(g(x))](https://oeis.org/A239763)

[f(f(f(x))) = f(g(x))](https://oeis.org/A239764)

[f(f(x)) = f(g(g(x)))](https://oeis.org/A239766)

[f(x) = f(g(f(x)))](https://oeis.org/A239768)

[f(g(f(x))) = g(f(f(x))](https://oeis.org/A239770)

[f(f(x)) = f(g(f(x)))](https://oeis.org/A239772)

[f(f(g(x))) = f(f(f(x)))](https://oeis.org/A239774)

[f(f(g(x))) = f(f(x))](https://oeis.org/A239775)

[f(f(g(x))) = g(g(f(x)))](https://oeis.org/A239776)

[f(x) = f(g(g(x)))](https://oeis.org/A239777)

[f(f(f(x))) = f(g(g(x)))](https://oeis.org/A239778)

[f(g(g(x))) = g(g(f(x)))](https://oeis.org/A239779)

[f(g(f(x))) = f(f(g(x)))](https://oeis.org/A239782)

[f(g(x)) = f(g(f(x)))](https://oeis.org/A239783)

[f(g(g(x))) = f(g(f(x)))](https://oeis.org/A239784)

[f(f(x)) = f(f(f(x)))](https://oeis.org/A000949)

##Over all permutation functions

[f(g(g(x))) = g(f(f(x)))](https://oeis.org/A239836)

[f(g(g(x))) = g(g(f(x)))](https://oeis.org/A239841)

[f(x) = f(g(g(x)))](https://oeis.org/A239840)

[f(f(x)) = g(f(g(x)))](https://oeis.org/A239837)

[f(f(f(x))) = g(g(g(x)))](https://oeis.org/A239838)

[f(f(f(x))) = g(f(g(x)))](https://oeis.org/A239839)

[f(g(x)) = g(g(f(x)))](https://oeis.org/A088311)

