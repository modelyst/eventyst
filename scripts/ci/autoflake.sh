#!/usr/bin/env bash


#   Copyright 2022 Modelyst LLC
#   All Rights Reserved


autoflake \
    --remove-all-unused-imports \
    --in-place \
    --ignore-init-module-imports \
    -r \
    src/eventyst \
    tests
