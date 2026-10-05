#!/bin/sh
#git log | cat
git diff 4b825dc642cb6eb9a060e54bf8d69288fbee4904 `git ls-files` | cat
