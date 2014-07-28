---
layout: post
title:  "Transformation Analogues of Permutations"
date:   2014-07-28 13:00:00
categories: combinatorics transformations permutations
---

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

##Monogenic sizes


The histogram of single transformation generated (monogenic) semigroup sizes. The first column is [OEIS_A000248](http://oeis.org/A000248), these are the idempotent transformations.

One theme that will come up reguarly is the connection between transformation composition and trees. OEIS_A00248 also counts forests with n nodes and height at most one.

Another way to view idempotent transformations is to partition the transformation elements into k nonempty parts, then designate a representitive of each to send all the other elements within that partition to. 

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

##Lolipop graphs of monogenic transformations

So what do monogenic transformation semigroups look like? Sort of like a lolipop. They have a tail then enter a cycle. The length of the tail is refered to as the index, and the length of the cycle is referred to as the period.  Permutations are transformations with index zero. We can think of the tail as where elements get anhilated, and the cycle as when we reach a steady state number of elements.


Here is the lolipop generation graph triangle of cycle lengths 
First column is [OEIS_A000272](https://oeis.org/A000272) 
Second column is [OEIS_A163951](https://oeis.org/A163951) 
Third column is [OEIS_A163952](https://oeis.org/A163952) 
Triangle is provisionally [OEIS_A222029](https://oeis.org/A222029) 

{% highlight ruby %}

counting_numbers = Enumerator.new do |yielder|
  (0..1.0/0).each do |number|
    yielder.yield number
  end
end

def trans_mult(transa, transb)
  trans_ret = Array.new
  0.upto(transa.length-1) do |index|
    trans_ret.push(transa[transb[index]])
  end
  return trans_ret
end

def lolipop(trans)
  trans_hash ={}
  trans_hash[trans.clone] =0
  index = 1
  trans_current = trans_mult(trans, trans)
  while  trans_hash[trans_current] == nil
    trans_hash[trans_current.clone] = index
    index = index +1
    trans_current = trans_mult(trans_current, trans)
  end
  cycle_length =trans_hash.size - trans_hash[trans_current]
  return [trans_hash.size, cycle_length]
end

1.upto(10) do |index|
  tran_size =index
  histo_hash = {}
  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
    size, cycle_length = lolipop(x)
    #tail_length = size-cycle_length
    if (histo_hash[cycle_length] == nil)
      histo_hash[cycle_length] =1
    else
      histo_hash[cycle_length] = histo_hash[cycle_length]+1
    end
  }
  puts "#{tran_size}|" + histo_hash.inspect
end
#Output:
#1|{1=>1}
#2|{1=>3, 2=>1}
#3|{1=>16, 2=>9, 3=>2}
#4|{1=>125, 2=>93, 3=>32, 4=>6}
#5|{1=>1296, 2=>1155, 3=>480, 4=>150, 6=>20, 5=>24}
#6|{1=>16807, 2=>17025, 3=>7880, 4=>3240, 6=>840, 5=>864}
#7|{1=>262144, 2=>292383, 3=>145320, 4=>71610, 6=>26250, 5=>24192, 10=>504, 12=>420, 7=>720}
#8|{1=>4782969, 2=>5752131, 3=>3009888, 4=>1692180, 6=>773920, 5=>653184, 10=>32256, 12=>26880, 7=>46080, 15=>2688, 8=>5040}


 {% endhighlight %}


Looking at the histogram of lolipop tail lengths for transformations generated by a single element 
The first column is [OEIS_A006153](http://oeis.org/A006153) 
The table is OEIS provisionally http://oeis.org/A225540 

{% highlight ruby %}
counting_numbers = Enumerator.new do |yielder|
  (0..1.0/0).each do |number|
    yielder.yield number
  end
end

def trans_mult(transa, transb)
  trans_ret = Array.new
  0.upto(transa.length-1) do |index|
    trans_ret.push(transa[transb[index]])
  end
  return trans_ret
end

def lolipop(trans)
  trans_hash ={}
  trans_hash[trans.clone] =0
  index = 1
  trans_current = trans_mult(trans, trans)
  while  trans_hash[trans_current] == nil
    trans_hash[trans_current.clone] = index
    index = index +1
    trans_current = trans_mult(trans_current, trans)
  end
  cycle_length =trans_hash.size - trans_hash[trans_current]
  return [trans_hash.size, cycle_length]
end

1.upto(10) do |index|
  tran_size =index
  histo_hash = {}
  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
    size, cycle_length = lolipop(x)
    #tail_length = size-cycle_length
    if (histo_hash[size-cycle_length] == nil)
      histo_hash[size-cycle_length] =1
    else
      histo_hash[size-cycle_length] = histo_hash[size-cycle_length]+1
    end
  }
  puts "#{tran_size}|" + histo_hash.inspect
end
#Output:
#1|{0=>1}
#2|{0=>4}
#3|{0=>21, 1=>6}
#4|{0=>148, 1=>84, 2=>24}
#5|{0=>1305, 1=>1160, 2=>540, 3=>120}
#6|{0=>13806, 1=>17610, 2=>10560, 3=>3960, 4=>720}
#7|{0=>170401, 1=>296772, 2=>214410, 3=>104160, 4=>32760, 5=>5040}
#8|{0=>2403640, 1=>5536440, 2=>4692576, 3=>2686320, 4=>1115520, 5=>302400, 6=>40320}
#9|{0=>38143377, 1=>113680800, 2=>111488328, 3=>72080064, 4=>35637840, 5=>12942720, 6=>3084480, 7=>362880}
#10|{0=>672552730, 1=>2553111990, 2=>2872039680, 3=>2053089360, 4=>1147184640, 5=>501832800, 6=>162086400, 7=>34473600, 8=>3628800}

 {% endhighlight %}


##Transformations with k outputs 
[OEIS_A090657](http://oeis.org/A090657)

{% highlight ruby %}
counting_numbers = Enumerator.new do |yielder|
  (0..1.0/0).each do |number|
    yielder.yield number
  end
end

0.upto(7) do |index|
  tran_size =index
  counts = []
  0.upto(index) do
    counts.push(0)
  end

  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
      counts[x.uniq.length] = counts[x.uniq.length] +1
   }
   puts index.inspect + "|" + counts.inspect  #  + "|" + counts.inject(:+).inspect     + "|" + (index**index).inspect

end
#Output:
#0|[1]
#1|[0, 1]
#2|[0, 2, 2]
#3|[0, 3, 18, 6]
#4|[0, 4, 84, 144, 24]
#5|[0, 5, 300, 1500, 1200, 120]
#6|[0, 6, 930, 10800, 23400, 10800, 720]
#7|[0, 7, 2646, 63210, 294000, 352800, 105840, 5040]
{% endhighlight %}




##Closed subsets 
[OEIS_A001865](http://oeis.org/A001865) second column 

[OEIS_A065456](http://oeis.org/A065456) third column 

1,18,305,5595 Forth column new to OEIS 

[OEIS_A060281](http://oeis.org/A060281) The entire triangle (without zeros)

{% highlight ruby %}
counting_numbers = Enumerator.new do |yielder|
  (0..1.0/0).each do |number|
    yielder.yield number
  end
end

# Hook and shortcut from  AN EFFICIENT PARALLEL BICONNECTIVITY ALGORITHM
#Tarjan and Vishkin
# http://www.umiacs.umd.edu/users/vishkin/TEACHING/ENEE759KS12/TV85.pdf

def partitions(trans)
  parent =Array.new()
  0.upto(trans.length-1) do |index|
    parent.push(index)
  end
  0.upto(trans.length-1) do |outer_index|
    0.upto(trans.length-1) do |index|
      #shortcut
      parent[index] = parent[parent[index]]
    end
    0.upto(trans.length-1) do |index|
      #hook
      if (parent[trans[index]] < parent[parent[index]])
        parent[parent[index]] = parent[trans[index]]
      end
      if (parent[index] < parent[parent[trans[index]]])
        parent[parent[trans[index]]] = parent[index]
      end
    end
  end
  return parent
end

0.upto(7) do |index|
  tran_size =index
  counts = []
  0.upto(index) do
    counts.push(0)
  end

  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
   counts[partitions(x).uniq.length] = counts[partitions(x).uniq.length] +1

  }
   puts index.inspect + "|" + counts.inspect  #  + "|" + counts.inject(:+).inspect     + "|" + (index**index).inspect

end
#Outputs:
#0|[1]
#1|[0, 1]
#2|[0, 3, 1]
#3|[0, 17, 9, 1]
#4|[0, 142, 95, 18, 1]
#5|[0, 1569, 1220, 305, 30, 1]
#6|[0, 21576, 18694, 5595, 745, 45, 1]

{% endhighlight %}


##Derangements for $T_{n} =  {(n-1)}^n$
[OEIS_A065440](http://oeis.org/A065440)
[OEIS_A007778](http://oeis.org/A007778) 
[Derangements (for permutations)](http://en.wikipedia.org/wiki/Derangement)

{% highlight ruby %}
counting_numbers = Enumerator.new do |yielder|
  (0..1.0/0).each do |number|     yielder.yield number
  end
end

def is_derangement(trans)
  0.upto(trans.length-1) do |index|
   if(trans[index] == index)
           return false
   end
  end
  return true
end

0.upto(10) do |index|
  tran_size =index
  count =0
  counting_numbers.take(tran_size).repeated_permutation(tran_size).each { |x|
    if (is_derangement(x))
      count = count +1
    end
  }
  puts "derangements(#{index}) #{count}"
end

{% endhighlight %}


[OEIS]:	https://oeis.org
[OEISA000312]:	https://oeis.org/A000312
[jekyll-gh]: https://github.com/mojombo/jekyll
[jekyll]:    http://jekyllrb.com
