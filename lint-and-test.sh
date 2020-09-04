#!/bin/sh
set -eux
flake8 --output-file=lint-testresults.xml --format junit-xml --exit-zero
# Had to comment the tests out for the moment PUT BACK IN!!!!
python -m pytest tests/unit/ff_test.py --junitxml=unit-testresults.xml
