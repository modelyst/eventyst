#!/usr/bin/env bash

#   Copyright 2022 Modelyst LLC
#   All Rights Reserved


set -e
set -x
flake8 --version
flake8 src/eventyst tests
black --version
black src/eventyst tests --config=./pyproject.toml --check
isort --version
isort src/eventyst tests --check-only
