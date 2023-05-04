#!/usr/bin/env bash


#   Copyright 2022 Modelyst LLC
#   All Rights Reserved


set -e
set -x

coverage run -m pytest tests
coverage report --show-missing
coverage xml
coverage html -d coverage
