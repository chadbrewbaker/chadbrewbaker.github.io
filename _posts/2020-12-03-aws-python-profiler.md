---
layout: post
title:  "REPL.it Review"
date:   2020-12-03 12:40:19
categories: 
---

# The AWS CodeGuru Profiler for AWS Lambda Python

I didn't see a source licence, so here is the incantation to look at it yourself:

```bash
curl $(aws lambda get-layer-version-by-arn --arn \
 arn:aws:lambda:us-east-1:157417159150:layer:AWSCodeGuruProfilerPythonAgentLambdaLayer:1 \
 --query Content.Location --output text) -o python_profiler.zip
```

It's worth a read for anyone that does performance critical Python programming. I learned a new trick to automatically garbage collect temporary objects:

```python
del foo
```

Only glaring performance issue I saw was that they aren't using dictionary compression. If you are goign to analyize your own tracers I would download zstd, and train it:

```bash
zstd --train FullPathToTrainingSet/* -o dictionaryName
```

I would expect at least an additional 25% savings in compression.

Can't wait to see the [Optimyze](https://optimyze.cloud/) solution when they roll out their tools for comparison.
