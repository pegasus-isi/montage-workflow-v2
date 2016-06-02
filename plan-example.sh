#!/bin/bash

set -e

export PYTHONPATH=`pegasus-config --python`:$PYTHONPATH

if ! which mProject >/dev/null 2>&1; then
    echo "Error: Unable to find the Montage tools in your path. Please download and" 1>&2
    echo "       install version 4 or above (http://montage.ipac.caltech.edu)" 1>&2
    exit 1
fi

if [ ! -e montage-workflow.py ]; then
    echo "Error: You have to run this script from the top level workflow checkout" 1>&2
    exit 1
fi
rm -rf data

./montage-workflow.py --center "56.5 23.75" --degrees 1.0 --band dss:DSS2B:blue --band dss:DSS2R:green --band dss:DSS2IR:red

pegasus-plan \
        --dir work \
        --relative-dir `date +'%s'` \
        --dax data/montage.dax \
        --sites condor_pool \
        --output-site local

