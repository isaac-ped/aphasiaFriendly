#!/usr/bin/env bash
# Helper script to run summarization on all inputs
mkdir -p finetuning
set -eu
for X in inputs/*.txt; do
    echo "###### Running on $X"
    BASENAME="$(basename "$X")"
    NAME="${BASENAME%.*}"
    ./af summarize -f yaml -f pptx "$X" "$@" -v;
    cp "output/$NAME/summary.yaml" "finetuning/$NAME.yaml"
done
