---
layout: post
title:  "co-Server Architecture"
date:   2016-4-03 12:38:19
categories: algebra haskell functional programming lambda function
---

A recent client opened my eyes up to something shocking. We don't need self managed servers.

Google's Firebase, AWS Lambda, and AWS S3/RDS/Elasticache/Dynamo are enough.

Lambda jobs can be triggered off a Git commit to build, run unit tests, deploy, and run integration tests. Jenkins is now obsolete.

Now monoliths are only for IOT devices which don't have the luxury of distrbiuting their workloads on other servers.

Rails and Django will no longer be monoliths but Lambda herding frameworks. "Hyperloop" framework anyone?

1) We need a new complexity metric. Purity. Mark every Operating System function call. Propigate the impurity taint to every function that calls them. What percentage of code is still pure? Adding an "impure" function identifer to C/C++ and having the compiler optionally enforce it would bring Haskell like discipline.

On [clang](https://t.co/XM1ML7gteu) we can do this with a litte bit of work.

On JVM this seems to be harder given the VM. One exists for [Scala](https://github.com/olhotak/scalacg).

For Ruby and Python this is going to be very painful. Whole swoths of the Ruby/Python VM will have to be purged of unnecisary mutable state. 

2) Amazon needs to release a LambdaServer Packer template. Somthing that you can run on a Linux box to serve up AWS Lambda functions without modification.

3) We need checkpoint in the JVM. Dump the entire JVM state to a binary file that is quick to restart from. The the stack/heap grow to the proper size, dump the contigious binary (possibly on multiple threads), wire up variables that need OS resource handles.  Same for C/C++ so in memory data structres can be pre-populated.

4) The processor in memory revolution is coming. By getting rid of impurity we have less code to refactor when going to these architectures. 
