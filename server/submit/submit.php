<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// 
// Licensed under the GNU Public License, version 2.

function add_data_to_db($utctime, $latitude, $longitude, $altitude, $speed) {

	// include connection data for mysql db
	require("../config/config.php");

	$mysql_connection = mysql_connect($mysql_server, $mysql_username, 
		$mysql_password);

	$mysql_insert_query = "INSERT INTO $mysql_table (name, utctime, "
		. "latitude, longitude, altitude, speed) VALUES (\"" 
		. mysql_real_escape_string($_SERVER['PHP_AUTH_USER']) 
		. "\", $utctime, $latitude, $longitude, $altitude, $speed);";
	$mysql_select_query = "SELECT * FROM $mysql_table WHERE name=\"" 
		. mysql_real_escape_string($_SERVER['PHP_AUTH_USER']) 
		. "\" AND utctime=$utctime";

	if($mysql_connection) {
		// use mysql database
		if(!mysql_select_db($mysql_database, $mysql_connection)) {
			// return 4 for "error mysql_select_db"
			return 4;
		}

		// get data to check duplicate entries
		$result = mysql_query($mysql_select_query);
		$row = mysql_fetch_row($result);
		if(count($row) !== 1) {
			// return 5 for "duplicate entries"
			return 5;
		}

		// insert data
		if(!mysql_query($mysql_insert_query)) {
			// return 3 for "error mysql_query"
			return 3;
		}

		// close connection
		if(!mysql_close($mysql_connection)) {
			// return 2 for "error mysql_close"
			return 2;
		}

		// print ok for the client
		// return 0 for "ok"
		return 0;
		}
	else {
		// print error message for client
		// return 1 for "error mysql_connect"
		return 1;
	}
}


if(isset($_SERVER['PHP_AUTH_USER']) 
	&& isset($_POST['latitude'])
	&& isset($_POST['longitude'])
	&& isset($_POST['utctime'])
	&& isset($_POST['altitude'])
	&& isset($_POST['speed'])) {

	// set initial error code
	$error_code = -1;

	// check if more than only one gps point is transmitted
	if(is_array($_POST['latitude'])
		&& is_array($_POST['longitude'])
		&& is_array($_POST['utctime'])
		&& is_array($_POST['altitude'])
		&& is_array($_POST['speed'])) {

		// check if all arrays have the same length
		if(count($_POST['latitude']) === count($_POST['longitude'])
			&& count($_POST['latitude']) === count($_POST['utctime'])
			&& count($_POST['latitude']) === count($_POST['altitude'])
			&& count($_POST['latitude']) === count($_POST['speed'])) {

			// add all POST data to db
			for($i = 0; $i < count($_POST['latitude']); $i++) {

				// sanitize POST data
				// Latitude in degrees: +/- signifies West/East
				$latitude = doubleval($_POST['latitude'][$i]);
				// Longitude in degrees: +/- signifies North/South
				$longitude = doubleval($_POST['longitude'][$i]);
				$utctime = doubleval($_POST['utctime'][$i]);
				$altitude = doubleval($_POST['altitude'][$i]);
				$speed = doubleval($_POST['speed'][$i]);

				// add data to db
				$error_code = add_data_to_db($utctime, $latitude, 
					$longitude, $altitude, $speed);

				// ignore error code for "ok" and "duplicate entries"
				if($error_code != 0
					&& $error_code != 5) {
					break;
				}
			}
		}
		else {
			// error code for "error arrays_not_same_length"
			$error_code = 6;
		}
	}
	else {
		// sanitize POST data
		$latitude = doubleval($_POST['latitude']);
		$longitude = doubleval($_POST['longitude']);
		$utctime = doubleval($_POST['utctime']);
		$altitude = doubleval($_POST['altitude']);
		$speed = doubleval($_POST['speed']);

		// add data to db
		$error_code = add_data_to_db($utctime, $latitude, $longitude, 
			$altitude, $speed);
	}

	// print error message
	switch($error_code) {
		case 0:
			echo "ok";
			break;
		case 1:
			echo "error mysql_connect";
			break;
		case 2:
			echo "error mysql_close";
			break;
		case 3:
			echo "error mysql_query";
			break;
		case 4:
			echo "error mysql_select_db";
			break;
		case 5:
			echo "duplicate entries";
			break;
		case 6:
			echo "error arrays_not_same_length";
			break;
		}
}
else {
	echo "error data missing";
}

?>
