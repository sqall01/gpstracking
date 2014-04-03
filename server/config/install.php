<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// 
// Licensed under the GNU Public License, version 2.

// include connection data for mysql db
require_once("./config.php");

$mysql_connection = mysql_connect($mysql_server, $mysql_username, 
						$mysql_password);
if(!$mysql_connection) {
	echo "error mysql_connection";
	exit(1);				
}
if(!mysql_select_db($mysql_database, $mysql_connection)) {
	echo "error mysql_select_db";
	exit(1);
}

// create table
mysql_query('CREATE TABLE IF NOT EXISTS ' 
	. mysql_real_escape_string($mysql_table) . ' ('
	. 'name CHAR(30) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,'
	. 'utctime DOUBLE NOT NULL,'
	. 'latitude DOUBLE NOT NULL,'
	. 'longitude DOUBLE NOT NULL,'
	. 'altitude DOUBLE NOT NULL,'
	. 'speed DOUBLE NOT NULL,'
	. 'PRIMARY KEY(name, utctime)'
	. ');');

?>
