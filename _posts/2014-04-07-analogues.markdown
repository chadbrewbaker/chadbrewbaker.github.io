---
layout: post
title:  "Transformation Analogues of Permutations"
date:   2014-04-07 12:38:19
categories: combinatorics transformations permutations
---

DRAFT VERSION


Today we will go over some properties of transoformations that are similar to properties of permutations. 

Lets start with the most basic, the number of transformations on n elements, [OEIS_A000312](https://oeis.org/A000312).

$$a(n) = n^n $$

One ubiquitous equation involving permutations are the binomial coefficients. 
$${n\choose k} = {n!\over k! (n-k)!}$$

If we subsitute the factorial function for a(n) we get :

$${a(n)\over a(k) a(n-k)}$$

Combinatorially this equation takes all elements of order n then removes elements that match a pair consisting of one order k element and one order n-k element. By replacing a(n) with the number of transformations on n elements we obtain [OEIS_A069322](http://oeis.org/A069322).


$${n^{n}\over k^{k} (n-k)^{n-k}}$$


Another property of permutations is the [Eulerian numbers] (http://en.wikipedia.org/wiki/Eulerian_number), which count the number of elements that are greater than their previous element. For transformations they form [OEIS_A22573](https://www.oeis.org/A225753).

{% highlight ruby %}
def mono_runs(trans)
  count =1
  1.upto(trans.length-1) do |index|
    if (trans[index-1]>trans[index])
      count = count +1
    end
  end
  count
end
1.upto(10) do |index|
  tran_size =index
  counts = []
  0.upto(index) do
    counts.push(0)
  end
  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
    runs = mono_runs(x)
    counts[runs] = counts[runs]+1
  }
  puts index.inspect + "|" + counts.inspect # + "|" + counts.inject(:+).inspect
end
{% endhighlight %}







[OEIS]:	https://oeis.org
[OEISA000312]:	https://oeis.org/A000312
[jekyll-gh]: https://github.com/mojombo/jekyll
[jekyll]:    http://jekyllrb.com
