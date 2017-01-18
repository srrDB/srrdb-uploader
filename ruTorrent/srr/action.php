<?php
require_once( '../../php/rtorrent.php' );

ignore_user_abort(true);
set_time_limit(0);

if (!isset($HTTP_RAW_POST_DATA)) {
    $HTTP_RAW_POST_DATA = file_get_contents("php://input");
}

if (isset($HTTP_RAW_POST_DATA)) {
    exec(dirname(__FILE__).'/action.pl '.escapeshellarg($HTTP_RAW_POST_DATA).' 2>&1', $output, $status);
    cachedEcho($output[count($output)-1],"application/json");
}
?>
