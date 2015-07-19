#!/bin/sh

export PYTHONPATH=.

nosetests -w tests/ -v
