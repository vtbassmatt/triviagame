#!/bin/sh

# This should only be run by the Dockerfile for deployment to fly.io
commit=$(git rev-parse HEAD)
[ -n "$(git status --short)" ] && dirty=-dirty
printf "DEPLOYED_COMMIT = '$commit$dirty'"
printf "DEPLOYED_COMMIT = '$commit$dirty'" >triviagame/commit.py
