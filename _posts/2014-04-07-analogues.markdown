---
layout: post
title:  "Transformation Analogues of Permutations"
date:   2014-04-07 12:38:19
categories: combinatorics transformations permutations
---

Transformations, also known as endofunctions, are superset of permutations where repeated elements in the codomain are allowed. Composing transformations can be done with the same algorithm as permutations.

{% highlight ruby %}
def trans_mult(transa, transb)
  trans_ret = Array.new
  0.upto(transa.length-1) do |index|
    trans_ret.push(transa[transb[index]])
  end
  return trans_ret
end
{% endhighlight %}

My particiular interest in transformations is their application in sofware testing, but they are a ubiquitous concept in mathematics and sofware engineering.

As we play with transformations it will be nice to have the following enumerator that generates natural numbers starting at zero.

{% highlight ruby %}
counting_numbers = Enumerator.new do |yielder|
  (0..1.0/0).each do |number| 
  	yielder.yield number
  end
end
{% endhighlight %}

Now if we want to print all transformations of size k we can use an enumerator.

{% highlight ruby %}
counting_numbers.take(k).repeated_permutation(k).each{|t|
	puts t.inspect
}
{% endhighlight %}

A first question we should ask ourselves, "Since transformations are a superset of permutations, do they have any analogues?"

The answer is a resounding yes!

As we explore transformations and related mathematical structures many will be crossreferenced with their [OEIS][OEIS] sequence. I have a few dozen queued up so this should take a few posts :)


[OEIS]:	https://oeis.org
[jekyll-gh]: https://github.com/mojombo/jekyll
[jekyll]:    http://jekyllrb.com
