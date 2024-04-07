#!/usr/bin/env bash
# Helper script to run summarization on all inputs
for X in finetuning/*.yaml; do
    echo "###### Running on $X"
    ./af rerun -f yaml -f pptx "$X" -v;
done
