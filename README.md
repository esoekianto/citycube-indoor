# CityCube Indoor

Mapbox Maps Flutter v3 demo for NEXTAPP 26 / FlutterCon Berlin.

A Flutter app built on `mapbox_maps_flutter` 3.0.0 that shows an indoor map of
CityCube Berlin, the venue of NEXTAPP 26, across all four event levels, with
the Mapbox booth highlighted and a 3D car parked outside. It runs on iOS,
Android and web. A second page is the classic markers "get started" map.

The indoor page is a Flutter port of the Mapbox GL JS example
[Add an indoor map with custom data](https://docs.mapbox.com/mapbox-gl-js/example/indoor-mapping-custom-data/):
Mapbox Standard is loaded as the basemap and an indoor style fragment with
GeoJSON sources and layers (clip, fills, extruded walls and doors, labels,
POIs) is added as a style import. A floor selector switches levels and a
"Building" entry shows Standard's own 3D landmark model of the CityCube.

Two flight buttons frame the demo: one flies to Berlin Brandenburg Airport
and switches on Mapbox Standard's built-in indoor mapping (`showIndoor`) with
the SDK's native floor selector, the other flies back to the CityCube and
its custom venue data.

## Run it

You need a Mapbox public access token. Pass it at build time:

```bash
flutter run --dart-define=ACCESS_TOKEN=pk.your_public_token
```

Works with `-d chrome`, an iOS simulator or device, and an Android emulator or
device. In VS Code, put the same `--dart-define` in `.vscode/launch.json`
(that folder is git-ignored, so tokens stay local).

## Project layout

| Path | What it is |
| --- | --- |
| `lib/indoor_map_page.dart` | Indoor map page: loads the fragment, floor selector, Building view, 3D car. |
| `lib/markers_page.dart` | The markers getting-started map (San Francisco landmarks). |
| `tool/generate_citycube_fragment.py` | Generates the indoor fragments from a hand-traced plan. Edit positions here and rerun. |
| `assets/indoor/citycube_fragment.json` | Fragment used on web: venue registered through the style's `indoor` key, `is-active-floor` filters. |
| `assets/indoor/citycube_fragment_config.json` | Fragment used on iOS and Android: floor driven by an import config option. |
| `assets/indoor/indoor_fragment.json` | The original GL JS example venue, kept for reference. |
| `assets/models/sportcar.glb` | Car model from the SDK's model layer example. |

Regenerate the fragments after editing the plan:

```bash
python3 tool/generate_citycube_fragment.py
```

New or renamed asset files need a cold `flutter run`; edits to an existing
asset apply on hot restart on iOS and Android, but web needs a cold run.

## Why two fragments

Mapbox GL JS activates custom indoor venues declared with the style's
`indoor` key, so on web the engine owns the active floor and the page uses
the 3.0.0 `MapboxMap.indoor` API (floor-state stream, `selectFloor`). The
native Maps SDKs only activate indoor data that comes from Mapbox (Standard's
`showIndoor`, available on request), so on iOS and Android the fragment
filters floor layers with `["==", ["get", "floor_id"], ["config", "activeFloor"]]`
and the page sets that import config property instead. The selector UI and
the data are the same on every platform.

## Deploy the web build to GitHub Pages

`.github/workflows/deploy-web.yml` builds the web app on every push to
`main` and publishes it to GitHub Pages at `https://<user>.github.io/citycube-indoor/`
(the path follows the repository name).
One-time setup in the GitHub repository:

1. Settings, Pages, Build and deployment, Source: GitHub Actions.
2. Settings, Secrets and variables, Actions: add `MAPBOX_ACCESS_TOKEN` with a
   public token whose URL restriction is set to your Pages origin, for example
   `https://<user>.github.io`. The token is compiled into the published
   JavaScript, so restrict it and never use a secret token here.

Web gap in 3.0.0: annotation managers are not implemented yet, so the markers
page shows the map without markers on web. The indoor page is complete.

## Toolchain notes

- Flutter 3.44 with AGP 9: `android/build.gradle.kts` applies the Kotlin
  Gradle plugin to `mapbox_maps_flutter_mobile`, which expects AGP's built-in
  Kotlin that Flutter enables from 3.47. Remove the block once you move to
  Flutter 3.47+ with `android.builtInKotlin=true`.
- Xcode 27 has no Simulator app; open Device Hub (`open -a DeviceHub`) to see
  booted simulators.
- iOS deployment target is 15.0, the minimum Xcode 27 accepts.
