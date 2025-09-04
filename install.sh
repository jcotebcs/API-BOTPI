#!/usr/bin/env bash
# Set up a virtual environment and install API-BOTPI.
set -e
python3 -m venv .venv                # create virtual environment
source .venv/bin/activate            # activate it
pip install --upgrade pip            # ensure pip is up to date
pip install .                        # install package
echo "Installation complete. Activate the environment with 'source .venv/bin/activate'"
