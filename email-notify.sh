#!/bin/bash

export PATH=$PEGASUS_BIN_DIR:$PATH

cd $PEGASUS_SUBMIT_DIR

# use a temp file for the message body
TMPFILE=`mktemp -t pegasus-notification.XXXXXXXXXX` || exit 1

cat >>$TMPFILE <<EOF
The workflow issued a new event: $PEGASUS_EVENT

  $PEGASUS_SUBMIT_DIR
EOF

if [ "X$PEGASUS_EVENT" = "Xat_end" ]; then
    echo >>$TMPFILE
    #echo "Output from pegasus-statistics:" >>$TMPFILE
    #echo >>$TMPFILE
    #touch monitord.done
    #pegasus-statistics -q >>$TMPFILE 2>&1
else
    echo >>$TMPFILE
    echo "Output from pegasus-status:" >>$TMPFILE
    echo >>$TMPFILE
    pegasus-status -v >>$TMPFILE 2>&1
fi
echo >>$TMPFILE

MUTT_APPENDS=""
MAILX_ARGS=""

# workflow images in the start message
if [ "X$PEGASUS_EVENT" = "Xstart" ]; then
    DAG_FS=`du -s -b *-0.dag | awk '{print $1;}'`
    if [ $DAG_FS -lt 1000000 ]; then
        if [ ! -e dax.svg ]; then
            pegasus-graphviz -o dag.dot *-0.dag
            /usr/bin/dot -Tsvg -odag.svg dag.dot
            if [ -e dag.svg ]; then
                MUTT_APPENDS="$MUTT_APPENDS dag.svg"
                MAILX_ARGS="$MAILX_ARGS -a dag.svg"
            fi
        
            pegasus-graphviz -o dax.dot *.dax
            /usr/bin/dot -Tsvg -odax.svg dax.dot
            if [ -e dax.svg ]; then
                MUTT_APPENDS="$MUTT_APPENDS dax.svg"
                MAILX_ARGS="$MAILX_ARGS -a dax.svg"
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

