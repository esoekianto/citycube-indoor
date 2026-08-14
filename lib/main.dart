import 'package:flutter/material.dart';
import 'package:mapbox_maps_flutter/mapbox_maps_flutter.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  // Pass your access token to MapboxOptions so you can load a map
  String ACCESS_TOKEN = const String.fromEnvironment("ACCESS_TOKEN");
  MapboxOptions.setAccessToken(ACCESS_TOKEN);

  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(home: MapPage());
  }
}

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
  final Map<String, Landmark> _landmarksByAnnotationId = {};

  Future<void> _onMapCreated(MapboxMap mapboxMap) async {
    final manager = await mapboxMap.annotations.createCircleAnnotationManager();

    final created = await manager.createMulti([
      for (final landmark in landmarks)
        CircleAnnotationOptions(
          geometry: landmark.point,
          circleColor: landmark.color.toARGB32(),
          circleRadius: 10.0,
          circleStrokeColor: Colors.white.toARGB32(),
          circleStrokeWidth: 2.0,
        ),
    ]);

    for (var i = 0; i < created.length; i++) {
      final annotation = created[i];
      if (annotation != null) {
        _landmarksByAnnotationId[annotation.id] = landmarks[i];
      }
    }

    manager.tapEvents(onTap: (annotation) {
      final landmark = _landmarksByAnnotationId[annotation.id];
      if (landmark == null) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("${landmark.title}\n${landmark.subtitle}")),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Mapbox Get Started")),
      body: MapWidget(
        cameraOptions: CameraOptions(
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
