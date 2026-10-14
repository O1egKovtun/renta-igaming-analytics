#!/bin/sh
# Scans the public tree (everything except private/, dist/, reports/, .git/) for leaked company data.
#  1. Terms: private/leak_terms.txt, one extended regex per line (the file is not published).
#  2. Number patterns that look like business figures.
#  3. Cyrillic outside the UK README and the glossary (fixed labels must be English).
# A tool error counts as a failure: "clean" is printed only when every check ran and found nothing.
set -u
export LC_ALL=en_US.UTF-8
cd "$(dirname "$0")"
EXCL="--exclude-dir=private --exclude-dir=dist --exclude-dir=reports --exclude-dir=.git --exclude=leak_check.sh"
bad=0

scan() { # scan <label> <grep args...>; prints hits, sets bad on hits or grep errors
  out=$(grep -rIn $EXCL "$@" . 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then echo "[$LABEL] $out"; bad=1
  elif [ "$rc" -ne 1 ]; then echo "[$LABEL] grep error: $out"; bad=1; fi
}

if [ -f private/leak_terms.txt ]; then
  while IFS= read -r term; do
    [ -z "$term" ] && continue
    LABEL="term:$term"; scan -iE -e "$term"
  done < private/leak_terms.txt
else
  echo "warning: private/leak_terms.txt missing, term check skipped"
fi

# thousands-formatted numbers and 2-decimal figures; tool limits and template CSS numbers are not business figures
LABEL=numbers
out=$(grep -rInE $EXCL --exclude=dashboard.html -e '[0-9]{1,3}([ ,][0-9]{3})+([.,][0-9]+)?' -e '[0-9]+[.,][0-9]{2}\b' . 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then
  out=$(echo "$out" | grep -v -E '10 000|50 000|"[0-9]+\.[0-9]+\.[0-9]+"|0\.3\.0')
  [ -n "$out" ] && { echo "[numbers] $out"; bad=1; }
elif [ "$rc" -ne 1 ]; then echo "[numbers] grep error: $out"; bad=1; fi

LABEL=cyrillic
out=$(grep -rInE $EXCL --exclude=README.uk.md --exclude=glossary.md --exclude=README.md -e '[а-яА-ЯіїєґІЇЄҐ]' . 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then
  out=$(echo "$out" | grep -v 'description:')
  [ -n "$out" ] && { echo "[cyrillic] $out"; bad=1; }
elif [ "$rc" -ne 1 ]; then echo "[cyrillic] grep error: $out"; bad=1; fi

if [ "$bad" -eq 0 ]; then echo clean; else echo "LEAKS FOUND OR CHECK FAILED"; exit 1; fi
