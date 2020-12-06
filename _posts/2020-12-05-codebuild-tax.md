---
layout: post
title:  "The CodeBuild Tax"
date:   2020-12-05 12:38:19
categories: 
---

[AWS CodeBuild Pricing](https://aws.amazon.com/codebuild/pricing/)

[AWS EC2 Pricing](https://aws.amazon.com/ec2/pricing/on-demand/)

Instance Type | CodeBuild Price (hr)| EC2 Price (hr)
--- | --- | ---
7-8G	4vcpu x86| $0.01*60= $0.60 | $0.17
15-16G 8vcpu x86| $0.02*60= $1.20 | $0.34
16G	8vcpu arm64|  $0.015*60= $0.90  | $0.308
144G 74vcpu x86|  $0.20*60= $12.0 | $3.06



Ignoring image storage, you save 3-4x by provisioning your own EC2 Batch instead of using CodeBuild.

$0.00756 per hour is the cost of AWS Lambda at 128M. That's 22x less than the 8G 4vcpu EC2.

S3 is $0.005 per 1000 writes, $0.0004 per 1000 reads. No bandwidth cost for in-region transfers -1 kb vs 1 G is *the same price*. Storage is $0.023 per GB. Huge savings chunking small files and using compression.

For example [the zstd git repo](https://github.com/facebook/zstd) has 497 files and is 71224 KB, 69544 KB as a tarball, 56608 KB at zstd level 19. You save 99% of the access charges and 25% of the space.
