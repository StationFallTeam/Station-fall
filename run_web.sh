#!/usr/bin/env bash
set -e
mkdir -p build/web build/web-cache
python3 -m pygbag --cdn https://pygame-web.github.io/archives/0.9/ --version 0.9 .