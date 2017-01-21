---
layout: post
title:  "Endoscope roadmap for 2017"
date:   2017-01-21 12:38:19
categories: Endoscope
---

Here is the roadmap for the (endosope)[https://github.com/chadbrewbaker/endoscope] project in 2017.

The current status is generic endofunction chasing is wokring with concrete implementations of transformations, permutations, and integer operations mod n.

Right now I am flushing out the various graphs you can get from iterating endofunctions. SMT-LIB2 solver for MIN-DOM-SET is also working to get optimal lower bounds for brute force search problems.

What is left? First documenting all the integer sequences existing in Sloanes OEIS and adding those not yet there.

Second, finishing the graph generation. I expect some good insights from removing idempotents and looking at the MIN-DOM-SET. I expect to get some fundemental insight into matrix matrix mutliply. 

Third, embedding into the transformation semigroup. I'm less interested in smooshing down to the smallest $$N$$ and more interested in just having a concrete transformation to work with.  

Fourth, I've isolated the 80,000 or so function signatures that the LLVM compiler plus test suites generate. I deally I would like to have a data store of "all the endo functions we care about".   

Fifth, graphs from the full $$N\times N$$ multiplication table. Reordering into a cannonical multiplication table in blocks of monogenic connected components, defining an ordering on connected components, then figuring out a cannonical order for each block.

Sixth, studying pairwise chasing $$A\times B = C$$ where $$A,B,C$$ are monogenic connected component classes.  $$A\times A = A$$ is something that Endoscope already handles.  $$A\times B  = A$$ and $$B\times A = A$$ is the next level, and $$A\times B  = C$$ is the general case. Simply knowing the monogenic class interatction counts may be useful.

Seventh, caching sets. The minimal amount of elements you can store to generate the entire semigroup. The minimal amount of elements you can store to do all operations in less than $$k$$ multiplies. Minimum amount of elements you can store such that the average is $k$ multiplies.  Mimimum amount of elments need to store to have $$log(n)$$, $$sqrt(n)$$ multiplies.  Specifically caching sets for boolean matrix matrix multiply.

Eighth, endofunction isomorphism. In boolean matrix matrix multiply which elements are isomorphic in the semigroup via relableing? How hard is it to take a matrix and assertain it's cannonical label?

Nineth, map the "Brent Equations" with Endoscope. They are a generalization of Strassen style matrix matrix multiply. The optimal $$3\times3$$ MATMUL with only 23 matrix multiplies was found by hand using this method.

Tenth, map endofunction composition equalities with endoscope. $$f(g(x)) == g(h(x))$$ I've added sequences in OEIS for the smaller ones. Also, arithmatic functions with tree/DAG size up to $$K$$; storing a minimal cost represenitive for each. I think the state space is much sparser than we think. Idea is to have a lookup table of optimal circuits.   

