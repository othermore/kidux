<?php
// https://apt.kidux.org/usage/: the machines that follow the archive, behind
// the password the folder's .htaccess asks for (ci/publish-usage.sh).
//
// The counting is ci/usage.py's, kept with its data in a folder of the
// hosting that no site serves, kidux-usage/ in the account's home. Opening
// the page first keeps every day's log not kept yet, so that the history
// never depends on how long the hosting keeps its logs, then shows the
// numbers, today's so far among them.

$private = dirname(__DIR__, 2) . '/kidux-usage';
putenv('KIDUX_USAGE_DIR=' . $private . '/logs');
putenv('KIDUX_APT_HOSTING=' . $private . '/logs.netrc');
$usage = escapeshellarg($private . '/usage.py');

exec("/usr/bin/python3 $usage fetch 2>&1", $fetched, $fetch_failed);
exec("/usr/bin/python3 $usage report --today --html 2>&1", $page, $report_failed);

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
if ($report_failed) {
    http_response_code(500);
    echo "<pre>", htmlspecialchars(implode("\n", $page)), "</pre>";
    exit;
}
echo implode("\n", $page);
if ($fetch_failed) {
    echo "<pre>", htmlspecialchars(implode("\n", $fetched)), "</pre>";
}
