---
layout: post
title:  "Faster Clang"
date:   2018-07-05 12:38:19
categories: C, Clang
---
Sticky notes on web applicaion generation systems. Expect a lot of edits

Web application programming has gone full derp. Nobody can keep up with all the server frameworks, client frameworks, clouds, and data stores.

For a long time I have envisioned using two domain specific lanugages to generate web applications. One for the data model, and one for user interaction.  MySQL+Yesod+Angular, PostGres+Django+Android ... it would all "just work". You would then apply target specific transformations and voila full stack development with minimal tie in to any specific technology/vendor.


The https://www.jhipster.tech gets a long way there on the data side. For now it is still tied to a JVM server side ecosystem, but it renders to several web front end frameworks. It's JDL modeling language is a great first start. I need to delve in further to see how it departs from Yesod/Django/Rails models; but I see two things it still is lacking or I have overlooked. Authentication requirements of data elements and support beyond SQL RDBMS for AWS S3 style file stores; not to mention geolocation data types should probably be default. 

Other links:

Awesome WASM Langs:
https://github.com/appcypher/awesome-wasm-langs

Beyond Web 2.0: Django and Python in the Modern Web Ecosystem:
https://www.youtube.com/watch?v=M9puQrivfPg
Python bytecode interpreter in Javascript:
https://pybee.org/project/projects/bridges/batavia/

Full Stack Web Development in Haskell (GHCJS+React, also Yesod+Angular)
http://blog.wuzzeb.org/full-stack-web-haskell/index.html

C++ WASM
https://developer.mozilla.org/en-US/docs/WebAssembly/C_to_wasm

https://componenthouse.com/2018/02/15/how-to-make-angular-and-webassembly-work-together/

RustWASM
https://github.com/rustwasm

Ruby WASM
http://www.blacktm.com/blog/ruby-on-webassembly#the-wasm-ruby-gem

.Net WASM
https://github.com/aspnet/Blazor



