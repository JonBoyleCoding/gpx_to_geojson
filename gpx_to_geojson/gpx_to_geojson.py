import json
import sys
import datetime
from pathlib import Path

import gpxpy
import typer

app = typer.Typer()


@app.command()
def main(
	input_file: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False),
	output_file: Path = typer.Argument(..., file_okay=True, dir_okay=True),
	output_as_feature_collection: bool = typer.Option(
		False, help="Output as a FeatureCollection instead of a list of Features"
	),
	source_name: str = typer.Option(None, help="Name of the source of the data"),
	start_time: datetime.datetime = typer.Option(
		None, help="Start time of the track in UTC"
	),
	end_time: datetime.datetime = typer.Option(
		None, help="End time of the track in UTC"
	),
):
	with open(input_file, "r") as gpx_file:
		gpx = gpxpy.parse(gpx_file)

	geojson = []

	if start_time:
		start_time = start_time.replace(tzinfo=datetime.timezone.utc)

	if end_time:
		end_time = end_time.replace(tzinfo=datetime.timezone.utc)

	data_start_time = None
	data_end_time = None

	for track in gpx.tracks:
		for segment in track.segments:
			for point in segment.points:
				if point.time:
					pt_local = point.time
					pt_local = pt_local.replace(tzinfo=datetime.timezone.utc)

					if start_time and pt_local < start_time:
						continue

					if end_time and pt_local > end_time:
						continue

					if not data_start_time or pt_local < data_start_time:
						data_start_time = pt_local

					if not data_end_time or pt_local > data_end_time:
						data_end_time = pt_local

				else:
					pt_local = None

				geojson.append(
					{
						"type": "Feature",
						"geometry": {
							"type": "Point",
							"coordinates": [point.longitude, point.latitude],
						},
						"properties": {
							"timestamp": pt_local.timestamp() if pt_local else None,
							"source": source_name
							if source_name
							else input_file.parent.name,
							"confidence": 1.0,
							"label": "unknown",
						},
					}
				)

	if output_as_feature_collection:
		geojson = {
			"type": "FeatureCollection",
			"features": geojson,
		}

	if output_file.is_dir():
		output_filename = f"{input_file.stem}"

		if start_time:
			output_filename += f"_st-{start_time.strftime('%Y%m%dT%H%M%S')}"

		if end_time:
			output_filename += f"_et-{end_time.strftime('%Y%m%dT%H%M%S')}"

		output_filename += ".geojson"

		output_file = output_file / output_filename

	if len(geojson) != 0:
		with open(output_file, "w") as f:
			json.dump(
				geojson,
				f,
				indent=4,
			)

	print(f"{input_file} -- {data_start_time} -> {data_end_time}")


if __name__ == "__main__":
	sys.exit(app())
