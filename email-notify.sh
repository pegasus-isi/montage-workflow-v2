#!/bin/bash

export PATH=$PEGASUS_BIN_DIR:$PATH

cd $PEGASUS_SUBMIT_DIR

# use a temp file for the message body
TMPFILE=`mktemp -t pegasus-notification.XXXXXXXXXX` || exit 1

cat >>$TMPFILE <<EOF
The workflow in:

  $PEGASUS_SUBMIT_DIR

Below is output from pegasus-status.

EOF

pegasus-status -v >>$TMPFILE 2>&1
echo >>$TMPFILE

MUTT_APPENDS=""
MAILX_ARGS=""

# workflow images in the start message
if [ "X$PEGASUS_EVENT" = "Xstart" ]; then
    DAG_FS=`du -s -b *-0.dag | awk '{print $1;}'`
    if [ $DAG_FS -lt 1000000 ]; then
        if [ ! -e dax.png ]; then
            pegasus-graphviz -o dag.dot *-0.dag
            /usr/bin/dot -Tpng -odag.png dag.dot
            if [ -e dag.png ]; then
                MUTT_APPENDS="$MUTT_APPENDS dag.png"
                MAILX_ARGS="$MAILX_ARGS -a dag.png"
            fi
        
            pegasus-graphviz -o dax.dot *.dax
            /usr/bin/dot -Tpng -odax.png dax.dot
            if [ -e dax.png ]; then
                MUTT_APPENDS="$MUTT_APPENDS dax.png"
                MAILX_ARGS="$MAILX_ARGS -a dax.png"
            fi
        fi
    fi
fi

# prefer mutt, but fall back to mailx if we have to
if which mutt >/dev/null 2>&1; then
    if [ "x$MUTT_APPENDS" != "x" ]; then
        MUTT_APPENDS="-a $MUTT_APPENDS"
    fi
    cat $TMPFILE | mutt -s "Workflow event: $PEGASUS_EVENT  $PEGASUS_SUBMIT_DIR" $MUTT_APPENDS -- $USER
else
    cat $TMPFILE | mailx -s "Workflow event: $PEGASUS_EVENT  $PEGASUS_SUBMIT_DIR" $MAILX_ARGS $USER
fi

rm -f $TMPFILE

