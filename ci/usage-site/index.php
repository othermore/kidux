<?php
// https://apt.kidux.org/usage/: the machines that follow the archive, behind
// the password the folder's .htaccess asks for (ci/publish-usage.sh).
//
// The counting is ci/usage.py's, kept with its data in a folder of the
// hosting that no site serves, kidux-usage/ in the account's home. Opening
// any page first keeps every day's log not kept yet, so that the history
// never depends on how long the hosting keeps its logs; then usage.py makes
// the page asked for: the summary, the machines or one of them, the
// addresses or one of them, the packages they have, a query of the
// database, or its table as CSV.
// The query reaches usage.py in its environment, never on a command line.

$private = dirname(__DIR__, 2) . '/kidux-usage';
putenv('KIDUX_USAGE_DIR=' . $private . '/logs');
putenv('KIDUX_APT_HOSTING=' . $private . '/logs.netrc');
putenv('KIDUX_USAGE_LOGS=' . $private . '/logs.url');
$usage = '/usr/bin/python3 ' . escapeshellarg($private . '/usage.py');

$views = ['summary', 'ids', 'id', 'addresses', 'address', 'packages', 'sql', 'csv'];
$view = in_array($_GET['view'] ?? '', $views, true) ? $_GET['view'] : 'summary';
$value = (string) ($_GET['value'] ?? $_GET['example'] ?? '');
putenv('KIDUX_USAGE_SQL=' . (string) ($_POST['sql'] ?? ''));
// The page's toggle: the test machines counted as any other, or kept apart.
putenv('KIDUX_USAGE_TESTS=' . (($_GET['tests'] ?? '') === '1' ? '1' : ''));

exec("$usage fetch 2>&1", $fetched, $fetch_failed);

header('Cache-Control: no-store');
if ($view === 'csv') {
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="kidux-usage-' . date('Y-m-d') . '.csv"');
} else {
    header('Content-Type: text/html; charset=utf-8');
}
$command = "$usage page --today --view " . escapeshellarg($view) . ' --value ' . escapeshellarg($value);
passthru("$command 2>&1", $page_failed);
if ($fetch_failed && $view !== 'csv') {
    echo "<pre>", htmlspecialchars(implode("\n", $fetched)), "</pre>";
}
