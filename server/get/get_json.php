<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org)
// 
// Licensed under the GNU Public License, version 2.

// include connection data for mysql db
require_once("../config/config.php");

// check if mode is set
if(!isset($_GET['mode'])) {
	echo "no mode selected";
	exit(1);
}

$mysql_connection = mysql_connect($mysql_server, $mysql_username,
						$mysql_password);
if(!$mysql_connection) {
	echo "error mysql_connection";
	exit(1);				
}

switch($_GET['mode']) {
	// in this case only a point newer than a given time is outputed
	case "livetracking":

		// check if needed data is given
		if(isset($_GET['lasttime']) 
			&& isset($_GET["trackingdevice"])) {

			$lastTime = doubleval($_GET['lasttime']);

			// use mysql database
			if(!mysql_select_db($mysql_database, $mysql_connection)) {
				echo "error mysql_select_db";
				exit(1);
			}

			// get newest point (if exists)
			$result = mysql_query("select * from $mysql_table where " 
				. "utctime > $lastTime and name = \"" 
				. mysql_real_escape_string($_GET["trackingdevice"]) 
				. "\" order by utctime desc limit 1");
			$row = mysql_fetch_array($result);

			// check if no newer entry exists
			if($row == null) {
				// output empty json objects
				header('Content-type: application/json');
				echo "{}";
			}
			else {
				// get only values that should be outputed
				$output = array("name" => $row["name"],
					"utctime" => $row["utctime"],
					"latitude" => $row["latitude"],
					"longitude" => $row["longitude"],
					"altitude" => $row["altitude"],
					"speed" => $row["speed"]);

				// output entry as a json object
				header('Content-type: application/json');
				echo json_encode($output);
			}
		}
		else {
			echo '"lasttime" or "trackingdevice" not given';
			exit(1);
		}
		break;

	// in this case all gps entries will be given back 
	// within a specific time window
	case "view":

		// check if needed data is given
		if(isset($_GET["trackingdevice"])
			&& isset($_GET["starttime"])
			&& isset($_GET["endtime"])) {

			$starttime = doubleval($_GET['starttime']);
			$endtime = doubleval($_GET['endtime']);

			// use mysql database
			if(!mysql_select_db($mysql_database, $mysql_connection)) {
				echo "error mysql_select_db";
				exit(1);
			}

			// get all entries within the given time frame
			$result = mysql_query("select * from $mysql_table where " 
				. "utctime <= $endtime and utctime >= $starttime " 
				. "and name = \"" 
				. mysql_real_escape_string($_GET["trackingdevice"]) 
				. "\" order by utctime asc");

			// generate output array that contains all gps entries
			$output = array();
			while($row = mysql_fetch_array($result)) {
				// get only values that should be outputed
				$entry = array("name" => $row["name"],
					"utctime" => $row["utctime"],
					"latitude" => $row["latitude"],
					"longitude" => $row["longitude"],
					"altitude" => $row["altitude"],
					"speed" => $row["speed"]);

				array_push($output, $entry);
			}

			// output array as a json object
			header('Content-type: application/json');
			echo json_encode($output);
		}

		break;

	// mode is unknown
	default:
		echo "mode does not exist";
		exit(1);
}

?>