#!/bin/bash

for d in $(ls -d Gx*.lv2); do
    patch $d/Makefile < 0001-fix-makefile-for-cross-compilation.patch
done
