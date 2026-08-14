import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';

void main() {
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
  const Landmark(this.position, this.title, this.subtitle, this.hue);

  final LatLng position;
  final String title;
  final String subtitle;
  final double hue;
}

final List<Landmark> landmarks = [
  Landmark(
    const LatLng(37.7955, -122.3937),
    "Ferry Building",
    "Marketplace and transit hub on the Embarcadero",
    BitmapDescriptor.hueRed,
  ),
  Landmark(
    const LatLng(37.8199, -122.4783),
    "Golden Gate Bridge",
    "Iconic suspension bridge spanning the Golden Gate strait",
    BitmapDescriptor.hueOrange,
  ),
  Landmark(
    const LatLng(37.8267, -122.4230),
    "Alcatraz Island",
    "Former federal prison on an island in San Francisco Bay",
    BitmapDescriptor.hueAzure,
  ),
];

class MapPage extends StatefulWidget {
  const MapPage({super.key});

  @override
  State<MapPage> createState() => _MapPageState();
}

class _MapPageState extends State<MapPage> {
  late final Set<Marker> _markers;

  @override
  void initState() {
    super.initState();
    _markers = landmarks.map((landmark) {
      return Marker(
        markerId: MarkerId(landmark.title),
        position: landmark.position,
        icon: BitmapDescriptor.defaultMarkerWithHue(landmark.hue),
        onTap: () {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text("${landmark.title}\n${landmark.subtitle}")),
          );
        },
      );
    }).toSet();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Mapbox Get Started")),
      body: GoogleMap(
        initialCameraPosition: const CameraPosition(
          target: LatLng(37.8020, -122.4230),
          zoom: 11,
          bearing: 0,
          tilt: 0,
        ),
        markers: _markers,
      ),
    );
  }
}
