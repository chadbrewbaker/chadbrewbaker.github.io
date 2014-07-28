---
layout: post
title:  "Transformation Analogues of Permutations"
date:   2014-04-07 12:38:19
categories: combinatorics transformations permutations
---

DRAFT VERSION


We will go over some properties of transoformations that are similar to properties of permutations. 

Lets start with the most basic, the number of transformations on n elements, [OEIS_A000312](https://oeis.org/A000312).

$$a(n) = n^n $$

One ubiquitous equation involving permutations are the binomial coefficients. 
$${n\choose k} = {n!\over k! (n-k)!}$$

If we subsitute the factorial function for a(n) we get :

$${a(n)\over a(k) a(n-k)}$$

Combinatorially this equation takes all elements of order n then removes elements that match a pair consisting of one order k element and one order n-k element. By replacing a(n) with the number of transformations on n elements we obtain [OEIS_A069322](http://oeis.org/A069322).


$${n^{n}\over k^{k} (n-k)^{n-k}}$$



##Monotonic runs

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

##Monogenic sizes

The histogram of single transformation generated (monogenic) semigroup sizes. The first column is [OEIS_A000248](http://oeis.org/A000248), these are the idempotent transformations. 

One theme that will come up reguarly is the connection between transformation composition and trees. OEIS_A00248 also counts forests with n nodes and height at most one.

Another way to view idempotent transofrmations is to partition the transformation elements into k nonempty parts, then designate a representitive of each to send all the other elements within that partition to. 

The entire table is [OEIS_A225725](http://oeis.org/A225725).
 

{% highlight ruby %}

def trans_powers(trans)
  trans_hash ={}
  trans_hash[trans] =1
  last = 0
  trans_current = trans.clone
  while  trans_hash.size != last
    last = trans_hash.size
    trans_current = trans_mult(trans_current, trans)
    trans_hash[trans_current.clone] =1
  end
  return trans_hash.keys
end

0.upto(10).each do |tran_size|
  histo_hash = {}
  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
    size = trans_powers(x).length
    if (histo_hash[size] == nil)
      histo_hash[size] =1
    else
      histo_hash[size] = histo_hash[size]+1
    end
  }
  puts "#{tran_size}|" + histo_hash.inspect
end

#Output:
#0|{1=>1}
#1|{1=>1}
#2|{1=>3, 2=>1}
#3|{1=>10, 2=>15, 3=>2}
#4|{1=>41, 2=>129, 3=>80, 4=>6}
#5|{1=>196, 2=>1115, 3=>1260, 4=>510, 6=>20, 5=>24}
#6|{1=>1057, 2=>10395, 3=>17780, 4=>12840, 5=>3744, 6=>840}
#7|{1=>6322, 2=>105315, 3=>258510, 4=>264810, 5=>135492, 6=>47250, 7=>4920, 10=>504, 12=>420}
 {% endhighlight %}

##Unlabeled transformations



The number of unlabeled transoformations of $T_{n}$ is [OEIS_A001372](http://oeis.org/A001372).
{% highlight ruby %}
counting_numbers = Enumerator.new do |yielder|
  (0..1.0/0).each do |number|
    yielder.yield number
  end
end

def rebase_with_perm(trans, perm)
  arr =[]
  0.upto(trans.length-1) do |index|
    arr.push([perm[index], perm[trans[index]]])
  end
  result = Array.new(trans.length)
  arr.each { |x|
    result[x[0]] =x[1]
  }
  result
end

def cannonize(trans)
  counting_numbers = Enumerator.new do |yielder|
    (0..1.0/0).each do |number|
      yielder.yield number
    end
  end
  min = trans.clone
  counting_numbers.take(trans.length).permutation(trans.length).each { |perm|
    candidate = rebase_with_perm(trans, perm)
    if ((min.inspect <=> candidate.inspect) > 0)
      min = candidate
    end
  }
  return min
end

1.upto(7) do |index|
  tran_size =index
  stuff = []
  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
    s = cannonize(x).inspect
    stuff.push(s)
  }
  puts("#{index}| "+stuff.uniq.size.to_s)
end
#Outputs:
#1| 1
#2| 3
#3| 7
#4| 19
#5| 47
#6| 130
{% endhighlight %}

[OEIS]:	https://oeis.org
[OEISA000312]:	https://oeis.org/A000312
[jekyll-gh]: https://github.com/mojombo/jekyll
[jekyll]:    http://jekyllrb.com
