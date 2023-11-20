#!/usr/bin/env bash
# Helper script to run summarization on all inputs
#
for X in inputs/*.pdf; do
    echo "###### Running on $X"
    ./af summarize "$X" -v;
done
