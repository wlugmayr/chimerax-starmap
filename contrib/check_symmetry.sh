#!/bin/sh
PERL5LIB=`/usr/bin/dirname "$0"`
chmod +x "${PERL5LIB}"/make_NCS.pl
"${PERL5LIB}"/make_NCS.pl $*
