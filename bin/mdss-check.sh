#!/usr/bin/env bash

for dir in {1..12} ; do echo $dir ; ssh "mdss-$dir" "ls -d */" ; done

