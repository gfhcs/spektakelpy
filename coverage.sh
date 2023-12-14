#!/bin/bash

coverage run --branch -m unittest tests.lexing tests.parsing tests.validation tests.machine tests.translation tests.printing
coverage report
coverage html
