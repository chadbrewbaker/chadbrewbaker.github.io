---
layout: post
title:  "Specifiying Story Problems with Algebra and Haskell"
date:   2016-01-27 12:38:19
categories: algebra haskell functional programming
---

After having some success with my middle school age kids, I am interested in getting Functional Programming taught along side Algebra in the basic curriculum.

If you are intersted in funding it, I have put up a [crowdfunding campaign](https://experiment.com/projects/qdtrnfnbbbzjmefdeszd).

I'm going to keep this page updated with my basic notes. No story problems yet, just your vanilla Algebra operations and identities along with what they roughly translate into as data types and functions in Haskell. 


Sum
$$ A + B $$
{% highlight haskell %}
data X = A | B
f :: X -> Either A B
{% endhighlight %}

Product
$$ A \times B$$
{% highlight haskell %}
data X = X A B
f :: X -> (A, B)
{% endhighlight %}

Exponential
$$ B^{A} $$
{% highlight haskell %}
f :: A -> B
{% endhighlight %}

Derivative
$$ {d \over dx}(ax^{n}) = a \times n \times x^{n-1}$$
{% highlight haskell %}
data N = M | 1
f ::  (a, N -> x)
f' :: (a, N, M -> X)
{% endhighlight %}

Curry
$$ (a^{m})^{n} = a^{mn}$$

{% highlight haskell %}
curry :: n -> m -> a
curry' :: (n,m) -> a

{% endhighlight %}


Co-curry
$$ a^{m}b^{m} = (ab)^{m}$$

{% highlight haskell %}
f :: (m -> a, m -> b)
f' :: m -> (a,b)
{% endhighlight %}

Domain Splitting
$$a^{m}a^{n} = a^{m+n}$$
{% highlight haskell %}
data B = M | N
f :: (M -> a, N -> a)
f' :: B -> a
{% endhighlight %}

Function Domain Shrinking
$$ a^{m} \div a^{n} = a^{m-n}$$
{% highlight haskell %}
data M = B | N
f :: (M -> a) remove (N -> a)
f' :: B -> a 
{% endhighlight %}

Function Co-domain Shrinking
$$ a^{m} \div b^{m} = ({a \over b})^{m}$$
{% highlight haskell %}
data A = N | B
f :: (m -> A) remove (m -> B)
f' :: m -> N
{% endhighlight %}


