<?php
// The hosting's scheduled task, once a day: keep every day's log not kept
// yet, whether or not anybody opens https://apt.kidux.org/usage/
// (ci/publish-usage.sh). It lives beside ci/usage.py in kidux-usage/.

putenv('KIDUX_USAGE_DIR=' . __DIR__ . '/logs');
putenv('KIDUX_APT_HOSTING=' . __DIR__ . '/logs.netrc');
passthru('/usr/bin/python3 ' . escapeshellarg(__DIR__ . '/usage.py') . ' fetch 2>&1', $failed);
exit($failed);
