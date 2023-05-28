#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

poetry export --without-hashes --format=requirements.txt > requirements.txt
poetry build