#!/bin/bash

set -o nounset

declare -r WORKDIR='/opt/FullView'
declare -r CURL_ERROR=1
declare -r DUMP='latest-bview.gz'
declare -r DATABASE='subscribers.sqlite3'

declare -r ASES='ases.list'
declare -r ASES4='ases4.list'
declare -r ASES6='ases6.list'


dumpfile="${WORKDIR}/${DUMP}"

asesfile="${WORKDIR}/${ASES}"
ases4file="${WORKDIR}/${ASES4}"
ases6file="${WORKDIR}/${ASES6}"

trap "rm -f ${dumpfile}" 0 1 2 3 6 9 15

curl -s "https://data.ris.ripe.net/rrc01/${DUMP}" -o "${dumpfile}" || exit "${CURL_ERROR}"

dumptime="$(bgpdump -m -v -l ${dumpfile} | head -1 | cut -d'|' -f2)"

databasefile="${WORKDIR}/${DATABASE}"

bgpdump -m "${dumpfile}" 2> /dev/null | cut -d'|' -f6 | sort -u | sed -n -e 's/.*:.*\//v6 /p;s/.*\..*\//v4 /p' |\
    sort -t' ' -k1,1 -k3,3 -k2,2 | uniq -c | sed -n -e 's/^\s\+//p' |\
    sed -n -e "1s/.*/insert into prefixes values(${dumptime},\"\0/;:start;N;s/\n/;/;$ b next;b start;:next;s/\( v4 [0-9]\+\);\([0-9]\+ v6\)/\1\",\"\2/;s/\([0-9]\+\) v[46] \([0-9]\+\)/\2,\1/g;s/.*/\0\");/p" | sqlite3 -batch "${databasefile}"

bgpdump -m  "${dumpfile}" | cut -f6,7 -d'|' | sed -n -e 's/.*:.*|/v6,/;s/.*\..*|/v4,/;s/,.*\s\+/,/p' | tr -d '{' | tr -d '}' | sort -u > "${asesfile}"
ases4_count="$(cat ${asesfile} | grep 'v4' | cut -f2- -d, | tr , '\n' | sort -u | tee ${ases4file} | wc -l)"
ases6_count="$(cat ${asesfile} | grep 'v6' | cut -f2- -d, | tr , '\n' | sort -u | tee ${ases6file} | wc -l)"

ases4_only="$(grep -Fxv -f ${ases6file} ${ases4file} | wc -l)"
ases6_only="$(grep -Fxv -f ${ases4file} ${ases6file} | wc -l)"

ases4_32="$(grep -E '6553[6-9]|655[4-9][0-9]|65[6-9][0-9]{2}|6[6-9][0-9]{3}|[7-9][0-9]{4}|[1-9][0-9]{5,}' ${ases4file} | wc -l)"
ases6_32="$(grep -E '6553[6-9]|655[4-9][0-9]|65[6-9][0-9]{2}|6[6-9][0-9]{3}|[7-9][0-9]{4}|[1-9][0-9]{5,}' ${ases6file} | wc -l)"

sqlite3 -batch "${databasefile}" "insert into ases values(${dumptime},${ases4_count},${ases6_count},${ases4_only},${ases6_only},${ases4_32},${ases6_32});"

exit 0
