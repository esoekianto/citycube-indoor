import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:flutter/material.dart';
import 'package:mapbox_maps_flutter/mapbox_maps_flutter.dart';

// A landmark to show as a marker on the map, mirroring the
// MapLocation model used in the Android/iOS Google-to-Mapbox tutorials.
class Landmark {
  const Landmark(this.point, this.title, this.subtitle, this.color);

  final Point point;
  final String title;
  final String subtitle;
  final Color color;
}

final List<Landmark> landmarks = [
  Landmark(
    Point(coordinates: Position(-122.3937, 37.7955)),
    "Ferry Building",
    "Marketplace and transit hub on the Embarcadero",
    Colors.red,
  ),
  Landmark(
    Point(coordinates: Position(-122.4783, 37.8199)),
    "Golden Gate Bridge",
    "Iconic suspension bridge spanning the Golden Gate strait",
    Colors.orange,
  ),
  Landmark(
    Point(coordinates: Position(-122.4230, 37.8267)),
    "Alcatraz Island",
    "Former federal prison on an island in San Francisco Bay",
    Colors.blue,
  ),
];

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  Future<void> _onMapCreated(MapboxMap mapboxMap) async {
    // mapbox_maps_flutter 3.0.0-rc.1 renders the map on web, but its
    // annotation managers are not implemented there yet and throw
    // UnimplementedError. Skip the markers on web until that lands.
    if (kIsWeb) return;

    final circleManager =
        await mapboxMap.annotations.createCircleAnnotationManager();
    await circleManager.createMulti([
      for (final landmark in landmarks)
        CircleAnnotationOptions(
          geometry: landmark.point,
          circleColor: landmark.color.toARGB32(),
          circleRadius: 10.0,
          circleStrokeColor: Colors.white.toARGB32(),
          circleStrokeWidth: 2.0,
        ),
    ]);

    final pointManager =
        await mapboxMap.annotations.createPointAnnotationManager();
    await pointManager.createMulti([
      for (final landmark in landmarks)
        PointAnnotationOptions(
          geometry: landmark.point,
          textField: landmark.title,
          textSize: 13.0,
          textOffset: [0.0, 1.4],
          textHaloColor: Colors.white.toARGB32(),
          textHaloWidth: 1.5,
        ),
    ]);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Mapbox Get Started")),
      body: MapWidget(
        viewport: CameraViewportState(
          center: Point(coordinates: Position(-122.4230, 37.8020)),
          zoom: 11,
          bearing: 0,
          pitch: 0,
        ),
        onMapCreated: _onMapCreated,
      ),
    );
  }
}
