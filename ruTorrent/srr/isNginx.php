<?php
require_once( '../../php/rtorrent.php' );
cachedEcho('{"isNginx": "'.((preg_match('!nginx!i', $_SERVER['SERVER_SOFTWARE'])) ? '1' : '0').'"}', "application/json");
?>
