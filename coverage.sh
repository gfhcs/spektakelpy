#!/bin/bash

coverage run --branch -m unittest tests.lexing tests.parsing tests.validation tests.machine tests.translation
coverage report
coverage html
