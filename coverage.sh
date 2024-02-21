#!/bin/bash

coverage run --branch -m unittest tests.lexing tests.parsing tests.validation tests.machine tests.translation tests.printing tests.bisimilarity
coverage report
coverage html
