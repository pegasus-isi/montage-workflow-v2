#!/bin/bash

cd $PEGASUS_SUBMIT_DIR

# use the Pegasus provided notification script
eval `$PEGASUS_BIN_DIR/pegasus-config --sh-dump`
$PEGASUS_SHARE_DIR/notification/email

