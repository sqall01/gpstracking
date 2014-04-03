<?php

// written by sqall
// twitter: https://twitter.com/sqall01
// blog: http://blog.h4des.org
// 
// Licensed under the GNU Public License, version 2.

// include connection data for mysql db
require_once("../config/config.php");

// check if mode is set
if(!isset($_GET['mode'])) {
	echo "no mode selected";
	exit(1);
}
// check if mode exists
else {
	switch($_GET['mode']) {
		case "livetracking":
			break;
		case "view":

			// check if starttime and endtime are not set
			if(!(isset($_GET['starttime']) 
				&& isset($_GET['endtime']))) {
				echo "no starttime and endtime are selected";
				exit(1);
			}

			break;

		// mode is unknown
		default:
			echo "mode does not exist";
			exit(1);
	}
}

// check if trackingdevice is set
if(!isset($_GET['trackingdevice'])) {
	echo "no trackingdevice selected";
	exit(1);
}
// check if trackingdevice does exist
else {
	$mysql_connection = mysql_connect($mysql_server, $mysql_username, 
		$mysql_password);
	if(!$mysql_connection) {
		echo "error mysql_connection";
		exit(1);				
	}

	// use mysql database
	if(!mysql_select_db($mysql_database, $mysql_connection)) {
		echo "error mysql_select_db";
		exit(1);
	}

	$result = mysql_query("select * from $mysql_table where name = \"" 
				. mysql_real_escape_string($_GET["trackingdevice"]) 
				. "\" limit 1");
	$row = mysql_fetch_array($result);

	// check if entry exists
	if(empty($row)) {
		echo "trackingdevice does not exist";
		exit(1);
	}		
}
?>

<html>
	<body>

		<?php
			if($_GET['mode'] === "livetracking") {
				echo '<p id="lastKnown">Last known position: unknown</p>';
				echo '<hr />';
			}
		?>

		<div id="mapdiv"></div>

		<script src="./openlayers/OpenLayers.js"></script>

		<script>
			// set all global configuration variables
			var request = new XMLHttpRequest();
			var vector = new OpenLayers.Layer.Vector();
			var lastTime = 0;
			var startTime = 0;
			var endTime = 0;
			var markers = new OpenLayers.Layer.Markers("Markers");
			var pointsArray = [];
			var markersArray = [];
			zoom=16;
			<?php
				echo 'var mode = "' . htmlentities($_GET['mode'], ENT_QUOTES) 
					. '"' . "\n";
				echo 'var trackingdevice = "' 
					. htmlentities($_GET['trackingdevice'], ENT_QUOTES) 
					. '"' . "\n";

				// set startTime and endtime if set
				if(isset($_GET['starttime']) 
					&& isset($_GET['endtime'])) {
					echo 'startTime = ' . doubleval($_GET['starttime']) . "\n";
					echo 'endTime = ' . doubleval($_GET['endtime']) . "\n";
				}
			?>


			// processes the response of the server for live tracking
			// and sets all markers and points
			function processResponseLivetracking() {
				if (request.readyState == 4) {

					// get JSON response and parse it
					response = request.responseText;
					newPoint = JSON.parse(response);

					// check if no newer point exists
					if(newPoint.latitude == null
						|| newPoint.longitude == null) {
						return;
					}

					// set the time of the last set marker
					lastTime = newPoint.utctime;

					// create new marker from json object
					newLonLat = new OpenLayers.LonLat(newPoint.longitude, 
						newPoint.latitude).transform(
							// transform from WGS 1984
							// to Spherical Mercator Projection
							new OpenLayers.Projection("EPSG:4326"), 
								map.getProjectionObject() 
					);
					newMarker = new OpenLayers.Marker(newLonLat);

					// center map to new marker
					map.setCenter(newLonLat);

					// add new markter to existing markers
					markersArray.push(newMarker);

					// add new marker to map
					markers.addMarker(newMarker)

					// if markers array is larger than 20 markers 
					// remove first element
					if(markersArray.length > 20) {
						oldMarker = markersArray.shift();
						markers.removeMarker(oldMarker);
					}

					// create new point for lines from json object
					newPoint = new OpenLayers.Geometry.Point(
									newPoint.longitude, newPoint.latitude);
					newPoint.transform(
						new OpenLayers.Projection("EPSG:4326"),
						new OpenLayers.Projection("EPSG:900913")
					);

					// add new point to existing points
					pointsArray.push(newPoint);

					// if points array is larger than 20 points 
					// remove first element
					if(pointsArray.length > 20) {
						pointsArray.shift();
					}
					
					// generate new features for vector layer (lineString)
					newFeatures = [];
					styleBlack = {strokeColor: "#000000", 
						strokeOpacity: 1, strokeWidth: 6};
					newFeatures.push(new OpenLayers.Feature.Vector(
						new OpenLayers.Geometry.LineString(pointsArray), 
						null, styleBlack));

					// remove old features
					vector.removeFeatures(vector.features);

					// add new feature
					vector.addFeatures(newFeatures);

					// generate local date from utc timestamp
					utcDate = new Date(lastTime * 1000);
					localDate = new Date(Date.UTC(utcDate.getFullYear(), 
						utcDate.getMonth(), utcDate.getDate(), 
						utcDate.getHours(), utcDate.getMinutes(), 
						utcDate.getSeconds(), utcDate.getMilliseconds()));

					// format date
					yearString = localDate.getFullYear();
					monthString = ("0" + (localDate.getMonth() + 1)).slice(-2);
					dateString = ("0" + localDate.getDate()).slice(-2);
					hoursString = ("0" + localDate.getHours()).slice(-2);
					minutesString = ("0" + localDate.getMinutes()).slice(-2);
					secondsString = ("0" + localDate.getSeconds()).slice(-2);

					// update last known location
					document.getElementById("lastKnown").innerHTML=
						"Last known position: " + monthString + "/" 
						+ dateString + "/" + yearString + " - " 
						+ hoursString + ":" + minutesString + ":" 
						+ secondsString;
				}
			}


			// requests the data for live tracking
			function requestLivetrackingData() {
				url = "./get_json.php?mode=" + mode + "&lasttime=" 
					+ lastTime + "&trackingdevice=" + trackingdevice;
				request.open("GET", url, true);
				request.onreadystatechange = processResponseLivetracking;
				request.send(null);
				// wait 10 seconds before requesting the next datapoint
				window.setTimeout("requestLivetrackingData()", 10000);		
			}


			// processes the response of the server for viewing
			// and sets all markers and points
			function processResponseView() {
				if (request.readyState == 4) {

					// get JSON response and parse it
					response = request.responseText;
					newPoints = JSON.parse(response);

					// check if response is empty
					if(newPoints[0] == null) {
						return;
					}

					// add all markers and generate points for lines
					for(i=0; i<newPoints.length; i++) {

						// create new marker from json object
						newLonLat = new OpenLayers.LonLat(
							newPoints[i].longitude, 
							newPoints[i].latitude).transform(
								// transform from WGS 1984
								// to Spherical Mercator Projection
								new OpenLayers.Projection("EPSG:4326"), 
									map.getProjectionObject() 
						);
						newMarker = new OpenLayers.Marker(newLonLat);

						// add new marker to map
						markers.addMarker(newMarker)

						// create new point for lines from json object
						newPoint = new OpenLayers.Geometry.Point(
							newPoints[i].longitude, newPoints[i].latitude);
						newPoint.transform(
							new OpenLayers.Projection("EPSG:4326"),
							new OpenLayers.Projection("EPSG:900913")
						);

						// add new point to existing points
						pointsArray.push(newPoint);							
					}

					// generate new features for vector layer (lineString)
					newFeatures = [];
					styleBlack = {strokeColor: "#000000", 
						strokeOpacity: 1, strokeWidth: 6};
					newFeatures.push(new OpenLayers.Feature.Vector(
						new OpenLayers.Geometry.LineString(pointsArray), 
						null, styleBlack));

					// add new feature
					vector.addFeatures(newFeatures);

					// center map to last marker
					map.setCenter(newLonLat);
				}
			}


			// requests the data for viewing
			function requestViewData() {
				url = "./get_json.php?mode=" + mode + "&starttime=" 
					+ startTime + "&endtime=" + endTime + "&trackingdevice=" 
					+ trackingdevice;
				request.open("GET", url, true);
				request.onreadystatechange = processResponseView;
				request.send(null);
			}			

			// generate map and layers
			map = new OpenLayers.Map("mapdiv");
			map.addLayer(new OpenLayers.Layer.OSM());
			map.addLayer(markers);
			map.addLayers([vector]);
			map.setCenter(null, zoom);
		

			if(mode == "livetracking") {
				// request first location for live tracking
				requestLivetrackingData();
			}
			else if(mode == "view") {
				// request locations for viewing mode
				requestViewData();				
			}
		</script>


	</body>
</html>