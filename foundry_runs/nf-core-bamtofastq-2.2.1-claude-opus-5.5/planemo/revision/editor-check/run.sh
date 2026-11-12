#!/bin/bash
# Run under: flock /tmp/galaxy-arash-planemo.lock bash planemo/revision/editor-check/run.sh
D=planemo/revision/editor-check
date +%H:%M:%S > $D/start.txt
setsid planemo serve --galaxy_root ~/Galaxy/galaxy-arash --biocontainers --port 9191 --skip_client_build \
  galaxy-workflow.before-revision.gxwf.yml galaxy-workflow.gxwf.yml > $D/serve.log 2>&1 &
SP=$!
python3 -I $D/check_editor.py http://127.0.0.1:9191 $D/editor-messages.json > $D/check.log 2>&1
echo "check exit $?" >> $D/check.log
kill -TERM -- -$SP 2>/dev/null; sleep 20; kill -KILL -- -$SP 2>/dev/null
date +%H:%M:%S > $D/end.txt
