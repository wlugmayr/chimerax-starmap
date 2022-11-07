#!/bin/sh
# Cygwin needs full path
PERL5LIB=`/usr/bin/dirname "$0"`

# uname has /usr/bin or /bin
#if [ `/usr/bin/env uname -o` = "Cygwin" ]; then
#    PERL5LIB=`/usr/bin/cygpath "${PERL5LIB}"`
#fi
"${PERL5LIB}"/make_NCS.pl $*
