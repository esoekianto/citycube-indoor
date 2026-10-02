#!/usr/bin/env python3
"""Generate assets/indoor/citycube_fragment.json.

A schematic indoor map of CityCube Berlin (Messedamm 26, Berlin) for NEXTAPP 26,
covering all four event levels:

  1  Level 1 (Halls A): session rooms in two columns around a central aisle
  E  Mezzanine 1: entrance lobby with registration, wardrobe, T-shirt printing
  2  Level 2 (Hall B): stages, sponsor booths and lounges, from the detailed
     "NEXTAPP 26 - CityCube E02" plan
  3  Level 3: ring corridor around the atrium, speaker rooms and M rooms

Level 2 positions are pixels of the E02 plan drawing. The other levels come
from the public NEXTAPP floorplan graphic, which is that plan rotated 90
degrees, and are given as normalised (u, v) coordinates inside each level's
parallelogram. Everything is converted to lon/lat by fitting the hall onto the
building footprint seen on satellite imagery (and cross-checked against Messe
Berlin's level plan). It is meant to demo the indoor style, not to be survey
accurate.

Run:  python3 tool/generate_citycube_fragment.py
"""
import json
import math
from pathlib import Path

# --- Georeferencing -------------------------------------------------------
# Building center and orientation estimated from Mapbox satellite imagery.
CENTER_LON, CENTER_LAT = 13.27058, 52.50009
BUILDING_SIDE_M = 116.0        # the CityCube is roughly a 116 m square
PLAN_UP_BEARING = 33.0         # the plan's "up" (passage to hall 7) points NE

# Plan drawing: hall interior spans roughly x 270-960, y 150-740 px and the
# 100 m² "Games Capital" square is ~80 px wide, so ~8 px per metre.
PX_PER_M = 8.0
PLAN_CX, PLAN_CY = 615.0, 445.0   # plan pixel that maps onto the building center

_M_PER_DEG_LAT = 110540.0
_M_PER_DEG_LON = 111320.0 * math.cos(math.radians(CENTER_LAT))
_up = (math.sin(math.radians(PLAN_UP_BEARING)), math.cos(math.radians(PLAN_UP_BEARING)))
_right = (math.sin(math.radians(PLAN_UP_BEARING + 90)), math.cos(math.radians(PLAN_UP_BEARING + 90)))


def plan_to_lonlat(px, py):
    """Plan pixel -> [lon, lat]. Plan y grows downwards."""
    mx = (px - PLAN_CX) / PX_PER_M
    my = (PLAN_CY - py) / PX_PER_M
    east = mx * _right[0] + my * _up[0]
    north = mx * _right[1] + my * _up[1]
    return [round(CENTER_LON + east / _M_PER_DEG_LON, 7),
            round(CENTER_LAT + north / _M_PER_DEG_LAT, 7)]


def rect(x1, y1, x2, y2):
    return [[plan_to_lonlat(x1, y1), plan_to_lonlat(x2, y1), plan_to_lonlat(x2, y2),
             plan_to_lonlat(x1, y2), plan_to_lonlat(x1, y1)]]


def circle(cx, cy, r_px, n=20):
    pts = [plan_to_lonlat(cx + r_px * math.cos(2 * math.pi * i / n),
                          cy + r_px * math.sin(2 * math.pi * i / n)) for i in range(n)]
    return [pts + [pts[0]]]


def feature(geometry, **props):
    return {"type": "Feature", "properties": props, "geometry": geometry}


def polygon(coords, **props):
    return feature({"type": "Polygon", "coordinates": coords}, **props)


def point(px, py, **props):
    return feature({"type": "Point", "coordinates": plan_to_lonlat(px, py)}, **props)


def line(x1, y1, x2, y2, **props):
    return feature({"type": "LineString",
                    "coordinates": [plan_to_lonlat(x1, y1), plan_to_lonlat(x2, y2)]}, **props)


# Hall interior in plan pixels, used to place the schematic levels.
HALL_X1, HALL_Y1, HALL_X2, HALL_Y2 = 270, 150, 960, 740


def uv_to_plan(u, v, x1=HALL_X1, x2=HALL_X2, y1=HALL_Y1, y2=HALL_Y2):
    """Schematic (u right, v down) -> plan pixels. The public floorplan is the
    E02 plan rotated 90 degrees clockwise, so schematic down is plan right and
    schematic right is plan up."""
    return x1 + v * (x2 - x1), y1 + (1 - u) * (y2 - y1)


def uv_rect(u1, v1, u2, v2, **box):
    pts = [uv_to_plan(u1, v1, **box), uv_to_plan(u2, v1, **box),
           uv_to_plan(u2, v2, **box), uv_to_plan(u1, v2, **box)]
    ring = [plan_to_lonlat(*p) for p in pts]
    return [ring + [ring[0]]]


def uv_poly(uvs, **box):
    ring = [plan_to_lonlat(*uv_to_plan(u, v, **box)) for u, v in uvs]
    return [ring + [ring[0]]]


TRACKS = ["droidCon", "flutterCon", "react nativeCon", "swiftCon", "agentic codingCon",
          "xr developerCon", "masCon", "mobile game developerCon", "Cross-Framework"]
TRACK_ALIASES = {"reactCon": "react nativeCon", "agentic codeCon": "agentic codingCon",
                 "XRCon": "xr developerCon"}


def track_of(name):
    for alias, track in TRACK_ALIASES.items():
        if name.startswith(alias):
            return track
    for track in TRACKS:
        if name.startswith(track):
            return track
    return None


# --- Venue metadata -------------------------------------------------------
half = BUILDING_SIDE_M / 2 * PX_PER_M
footprint = rect(PLAN_CX - half, PLAN_CY - half, PLAN_CX + half, PLAN_CY + half)

FLOORS = [  # id, name, description, z_index, default
    ("l1", "1", "Level 1 (Halls A): session rooms", 0, False),
    ("entrance", "E", "Mezzanine 1: entrance lobby and registration", 1, False),
    ("l2", "2", "Level 2 (Hall B): stages and sponsor area", 2, True),
    ("l3", "3", "Level 3: speaker rooms and M rooms", 3, False),
]

metadata = [polygon(footprint, id="citycube", type="structure", name="CityCube Berlin",
                    center_lon=CENTER_LON, center_lat=CENTER_LAT,
                    camera_zoom=18.0, camera_pitch=55, camera_bearing=PLAN_UP_BEARING)]
for fid, name, desc, z, default in FLOORS:
    others = ";".join(f[0] for f in FLOORS if f[0] != fid)
    metadata.append(polygon(footprint, id=fid, name=name, description=desc, type="floor",
                            z_index=z, is_default=default, structure_ids="citycube",
                            conflicted_floor_ids=others))

# --- Level 2 (Hall B): the exhibition floor -------------------------------
rooms, doors, pois = [], [], []
E02 = "l2"


def booth(x1, y1, x2, y2, number, name, category="booth"):
    rooms.append(polygon(rect(x1, y1, x2, y2), floor_id=E02, category=category,
                         name=name, booth=str(number)))


def area(coords, name, category, floor_id=E02, **extra):
    props = dict(floor_id=floor_id, category=category, name=name, **extra)
    track = track_of(name)
    if track and category in ("stage", "hall"):
        props["track"] = track
    rooms.append(polygon(coords, **props))


# Stages: seating block plus a raised platform.
for name, seats, seating, platform in [
    ("agentic codeCon 2", 180, (295, 235, 400, 310), (315, 195, 385, 225)),
    ("reactCon 3", 140, (490, 235, 580, 300), (505, 195, 565, 225)),
    ("droidCon 3", 154, (860, 205, 915, 355), (930, 255, 960, 305)),
    ("flutterCon 3", 180, (290, 605, 395, 705), (310, 715, 380, 745)),
    ("XRCon 1", 140, (620, 620, 715, 705), (640, 715, 700, 745)),
    ("swiftCon 3", 140, (850, 620, 950, 705), (870, 715, 935, 745)),
]:
    area(rect(*seating), name, "stage", seats=seats)
    area(rect(*platform), "Stage", "platform")

# Sponsor booths, numbered as on the plan.
booth(570, 325, 605, 347, 47, "Zalando")
booth(570, 347, 605, 370, 48, "Expo")
booth(485, 360, 530, 400, 61, "Amazon")
booth(485, 425, 530, 450, "49a", "Firebase")
booth(485, 490, 530, 525, 49, "Flutter")
booth(405, 458, 435, 483, 51, "Touchlab")
booth(435, 458, 465, 483, 50, "Codemate")
booth(405, 492, 435, 517, 52, "Leancode")
booth(435, 492, 465, 517, 53, "VGV")
booth(420, 368, 445, 385, "60a", "Callstack")
booth(420, 388, 445, 405, 59, "Zimperium")
booth(420, 408, 445, 425, "60b", "Software Mansion")
booth(622, 330, 640, 347, 41, "Posthog")
booth(642, 330, 660, 347, 42, "Berlindroid")
booth(622, 349, 640, 366, 43, "Gradle")
booth(642, 349, 660, 366, 44, "OneSpan")
booth(622, 368, 640, 385, 45, "Screenshotbot")
booth(642, 368, 660, 385, 46, "HolaFly")
booth(745, 318, 778, 340, 6, "Runway")
booth(782, 318, 815, 340, 5, "Porsche Digital")
booth(745, 343, 778, 365, 7, "Promon")
booth(782, 343, 815, 365, 8, "Mapbox", category="mapbox")
booth(685, 392, 715, 412, 24, "bitdrift")
booth(720, 392, 750, 412, 25, "Booth 25")
booth(685, 415, 715, 435, 23, "Zebra")
booth(720, 415, 750, 435, 22, "Bitrise")
booth(770, 392, 810, 425, "8a", "Harman")
booth(850, 390, 905, 450, 3, "AWS")
booth(770, 452, 810, 472, 9, "Touchlab")
booth(770, 475, 810, 495, 10, "Datadog")
booth(850, 480, 900, 525, 2, "RevenueCat")
booth(770, 522, 810, 542, 11, "Appdome")
booth(770, 545, 810, 565, 15, "Redcare Pharmacy")
booth(853, 555, 900, 590, 1, "JetBrains")
booth(690, 470, 712, 488, 29, "Maestro")
booth(716, 470, 738, 488, 26, "Appvestor")
booth(690, 491, 712, 509, 28, "Wolt")
booth(716, 491, 738, 509, 27, "Sentry")
booth(690, 545, 715, 568, 20, "Guardsquare")
booth(720, 545, 750, 568, 21, "eshard")
booth(690, 575, 715, 598, 19, "Scanbot")
booth(720, 575, 750, 598, 18, "Appetize")
booth(460, 625, 540, 705, 54, "Games Capital Berlin", category="games")

# Lounges and activities.
area(circle(632, 490, 35), "Networking Hub", "hub")
for name, cx, cy in [("reactCon Lounge", 630, 425), ("droidCon Lounge", 700, 458),
                     ("swiftCon Lounge", 695, 522), ("gamedev & xrCon Lounge", 640, 585),
                     ("flutterCon Lounge", 562, 545), ("agentic codeCon Lounge", 560, 470)]:
    area(circle(cx, cy, 16, n=12), name, "lounge")
area(circle(350, 485, 35), "Unsolved Unconference", "lounge")
area(rect(175, 150, 262, 330), "Food Court", "service")
area(rect(300, 365, 400, 405), "Badminton", "activity")
area(rect(695, 205, 790, 255), "Kicker", "activity")
area(rect(612, 258, 650, 295), "Airhockey", "activity")
area(rect(330, 755, 470, 785), "Sponsor storage", "service")

# Doors and points of interest.
for x1, y1, x2, y2 in [(540, 742, 580, 742), (740, 742, 780, 742), (800, 150, 880, 150),
                       (270, 450, 270, 490)]:
    doors.append(line(x1, y1, x2, y2, floor_id=E02))
pois += [
    point(560, 748, floor_id=E02, type="entrance", icon="entrance", name="Main entrance"),
    point(760, 748, floor_id=E02, type="entrance", icon="entrance", name="Entrance"),
    point(840, 144, floor_id=E02, type="entrance", icon="entrance", name="Passage to hall 7"),
    point(495, 330, floor_id=E02, type="coffee", icon="cafe", name="Coffee cart"),
    point(735, 483, floor_id=E02, type="coffee", icon="cafe", name="Coffee cart"),
    point(925, 590, floor_id=E02, type="coffee", icon="cafe", name="Coffee cart"),
    point(798, 354, floor_id=E02, type="highlight", icon="marker", name="Mapbox"),
]

# --- Level 1 (Halls A): session rooms --------------------------------------
L1 = "l1"
for name, u1, v1, u2, v2 in [
    ("masCon", 0.00, 0.00, 0.32, 0.13),
    ("droidCon 1", 0.05, 0.19, 0.45, 0.40),
    ("react nativeCon 1", 0.05, 0.42, 0.42, 0.55),
    ("swiftCon 2", 0.05, 0.56, 0.42, 0.66),
    ("droidCon 2", 0.05, 0.68, 0.42, 0.79),
    ("react nativeCon 2", 0.58, 0.19, 0.92, 0.29),
    ("Cross-Framework", 0.58, 0.31, 0.92, 0.42),
    ("flutterCon 1", 0.58, 0.42, 0.92, 0.55),
    ("swiftCon 1", 0.58, 0.56, 0.92, 0.66),
    ("agentic codingCon 1", 0.58, 0.68, 0.92, 0.79),
    ("mobile game developerCon", 0.08, 0.84, 0.35, 0.97),
]:
    area(uv_rect(u1, v1, u2, v2), name, "hall", floor_id=L1)
area(uv_rect(0.45, 0.15, 0.58, 0.85), "Central aisle", "foyer", floor_id=L1)
area(uv_rect(0.35, -0.14, 0.65, 0.0), "Food Court", "service", floor_id=L1)
area(uv_rect(0.00, 0.85, 0.06, 1.0), "West Lobby 1", "foyer", floor_id=L1)
pois += [
    point(*uv_to_plan(0.03, 0.92), floor_id=L1, type="entrance", icon="entrance",
          name="Entrance Jaffestrasse"),
    point(*uv_to_plan(0.97, 0.90), floor_id=L1, type="info", icon="information", name="East Lobby 1"),
]
doors.append(line(*uv_to_plan(0.0, 0.88), *uv_to_plan(0.0, 0.96), floor_id=L1))

# --- Mezzanine 1: entrance lobby -------------------------------------------
ENT = "entrance"
# The lobby is a strip along the Messedamm (plan right) side of the building.
LOBBY = dict(x1=700, x2=1060, y1=HALL_Y1, y2=HALL_Y2)
area(uv_poly([(0, 0), (1, 0), (1, 1), (0.72, 1), (0.72, 0.55), (0.40, 0.55), (0.40, 1), (0, 1)],
             **LOBBY), "Entrance Lobby", "foyer", floor_id=ENT)
area(uv_rect(0.38, 0.02, 0.72, 0.27, **LOBBY), "Registration", "service", floor_id=ENT)
area(uv_rect(0.03, 0.76, 0.28, 0.98, **LOBBY), "Wardrobe", "service", floor_id=ENT)
area(uv_rect(0.74, 0.42, 0.98, 0.98, **LOBBY), "T-Shirt Screen Printing", "activity", floor_id=ENT)
doors.append(line(*uv_to_plan(0.44, 0.55, **LOBBY), *uv_to_plan(0.68, 0.55, **LOBBY), floor_id=ENT))
pois += [
    point(*uv_to_plan(0.56, 0.62, **LOBBY), floor_id=ENT, type="entrance", icon="entrance",
          name="Entrance Messedamm"),
    point(*uv_to_plan(0.55, 0.14, **LOBBY), floor_id=ENT, type="info", icon="information",
          name="Registration"),
]

# --- Level 3: ring around the atrium --------------------------------------
L3 = "l3"
ring_outer = [plan_to_lonlat(*uv_to_plan(u, v)) for u, v in [(0, 0), (1, 0), (1, 1), (0, 1)]]
ring_inner = [plan_to_lonlat(*uv_to_plan(u, v)) for u, v in [(0.15, 0.2), (0.15, 0.8), (0.85, 0.8), (0.85, 0.2)]]
rooms.append(polygon([ring_outer + [ring_outer[0]], ring_inner + [ring_inner[0]]],
                     floor_id=L3, category="foyer", name="Level 3 corridor"))
area(uv_rect(0.20, 0.0, 0.75, 0.2), "Speaker Lounge & Prep Rooms", "service", floor_id=L3)
for name, u1, u2 in [("droidCon 5", 0.20, 0.40), ("droidCon 4", 0.40, 0.60),
                     ("flutterCon 4", 0.60, 0.80), ("flutterCon 2", 0.80, 1.00)]:
    area(uv_rect(u1, 0.8, u2, 1.0), name, "hall", floor_id=L3)
pois.append(point(*uv_to_plan(0.5, 0.9), floor_id=L3, type="info", icon="information",
                  name="East Lobby 3"))

# --- Style fragment -------------------------------------------------------
# Two variants of the same fragment are written:
#  * citycube_fragment.json: registers the venue through the style's `indoor`
#    key and filters floor layers with `is-active-floor`, like the GL JS
#    example. Mapbox GL JS activates custom venues, so the web build uses this
#    together with MapboxMap.indoor from mapbox_maps_flutter 3.0.0.
#  * citycube_fragment_config.json: drives the active floor through an import
#    config option instead. The native Maps SDKs only activate indoor data
#    from Mapbox (Standard's showIndoor, gated behind an access request), so
#    iOS and Android use this variant. "building" selects no floor at all.
TRACK_COLOR = ["match", ["get", "track"],
               "droidCon", "hsl(140, 60%, 80%)",
               "flutterCon", "hsl(200, 85%, 82%)",
               "react nativeCon", "hsl(270, 60%, 86%)",
               "swiftCon", "hsl(15, 85%, 82%)",
               "agentic codingCon", "hsl(35, 85%, 80%)",
               "xr developerCon", "hsl(320, 70%, 86%)",
               "masCon", "hsl(255, 60%, 86%)",
               "mobile game developerCon", "hsl(190, 70%, 84%)",
               "Cross-Framework", "hsl(230, 60%, 85%)",
               "hsl(300, 60%, 88%)"]
CATEGORY_COLOR = ["match", ["get", "category"],
                  "mapbox", "#4264fb",
                  "stage", TRACK_COLOR,
                  "hall", TRACK_COLOR,
                  "platform", "hsl(300, 40%, 72%)",
                  "lounge", "hsl(30, 75%, 85%)",
                  "hub", "hsl(20, 85%, 72%)",
                  "games", "hsl(150, 45%, 85%)",
                  "activity", "hsl(200, 70%, 86%)",
                  "service", "hsl(0, 0%, 90%)",
                  "foyer", "hsl(220, 20%, 94%)",
                  "hsl(220, 25%, 90%)"]
WALLED = ["in", ["get", "category"], ["literal", ["booth", "mapbox", "games", "service"]]]
DEFAULT_FLOOR = next(f[0] for f in FLOORS if f[4])


def build_fragment(native_indoor):
    if native_indoor:
        active = ["is-active-floor", ["get", "floor_id"]]
        clip_filter = ["is-active-floor"]          # clip only while a floor is shown
        venue = {"indoor": {"venue": {"sourceId": "indoor-metadata", "sourceLayers": []}}}
    else:
        active = ["==", ["get", "floor_id"], ["config", "activeFloor"]]
        clip_filter = ["!=", ["config", "activeFloor"], "building"]
        venue = {"schema": {"activeFloor": {"type": "string", "default": DEFAULT_FLOOR,
                                            "metadata": {"mapbox:title": "Active floor"}}}}

    def fc(features):
        return {"type": "geojson", "data": {"type": "FeatureCollection", "features": features}}

    return {
        "version": 8,
        "glyphs": "mapbox://fonts/mapbox/{fontstack}/{range}.pbf",
        "sprite": "mapbox://sprites/mapbox/streets-v12",
        **venue,
        "sources": {
            "indoor-metadata": fc(metadata),
            "indoor-structure": fc([polygon(footprint, id="citycube", name="CityCube Berlin")]),
            "indoor-floorplan": fc(rooms),
            "indoor-doors": fc(doors),
            "indoor-pois": fc(pois),
        },
        "layers": [
            {"id": "indoor-clip", "type": "clip", "source": "indoor-structure", "minzoom": 15,
             "filter": clip_filter, "layout": {"clip-layer-types": ["model", "symbol"]}},
            {"id": "indoor-structure-metadata", "type": "fill", "source": "indoor-metadata", "minzoom": 15,
             "paint": {"fill-opacity": 0, "fill-color": "#000000"}},
            {"id": "indoor-rooms", "type": "fill", "source": "indoor-floorplan", "minzoom": 15,
             "slot": "middle", "filter": active,
             "paint": {"fill-color": CATEGORY_COLOR, "fill-opacity": 1}},
            {"id": "indoor-platforms", "type": "fill-extrusion", "source": "indoor-floorplan", "minzoom": 15,
             "slot": "middle", "filter": ["all", active, ["==", ["get", "category"], "platform"]],
             "paint": {"fill-extrusion-height": 0.6, "fill-extrusion-color": "hsl(300, 40%, 72%)",
                       "fill-extrusion-cast-shadows": False}},
            {"id": "indoor-room-walls", "type": "fill-extrusion", "source": "indoor-floorplan", "minzoom": 15,
             "slot": "middle", "filter": ["all", active, WALLED],
             "paint": {"fill-extrusion-height": ["match", ["get", "category"], "mapbox", 3.5, "games", 1.2, 2.5],
                       "fill-extrusion-line-width": 0.2,
                       "fill-extrusion-color": ["match", ["get", "category"], "mapbox", "#4264fb", "hsl(0, 0%, 100%)"],
                       "fill-extrusion-cast-shadows": False}},
            {"id": "indoor-doors", "type": "fill-extrusion", "source": "indoor-doors", "minzoom": 15,
             "slot": "middle", "filter": active,
             "paint": {"fill-extrusion-height": 2.2, "fill-extrusion-line-width": 0.4,
                       "fill-extrusion-color": "hsl(28, 88%, 70%)", "fill-extrusion-cast-shadows": False}},
            {"id": "indoor-labels", "type": "symbol", "source": "indoor-floorplan", "minzoom": 15,
             # The Mapbox booth is labelled from its pin in indoor-pois instead.
             "filter": ["all", active, ["!", ["in", ["get", "category"], ["literal", ["platform", "mapbox"]]]]],
             "layout": {"text-field": ["to-string", ["get", "name"]],
                        "text-font": ["DIN Pro Medium", "Arial Unicode MS Regular"],
                        "text-size": ["match", ["get", "category"], "mapbox", 15, "stage", 13, "hall", 13, "hub", 13, "foyer", 14, 10],
                        "text-anchor": "center", "symbol-z-elevate": False,
                        # Lower keys are placed first, so stages keep their labels when neighbours collide.
                        "symbol-sort-key": ["match", ["get", "category"], "mapbox", 0, "stage", 1, "hall", 1, "hub", 1, 2]},
             "paint": {"text-color": ["match", ["get", "category"], "mapbox", "#4264fb", "hsl(210, 20%, 43%)"],
                       "text-halo-color": "#ffffff", "text-halo-width": 1.3}},
            {"id": "indoor-pois", "type": "symbol", "source": "indoor-pois", "minzoom": 15,
             "filter": active,
             "layout": {"icon-image": ["get", "icon"], "icon-size": 1, "icon-allow-overlap": True,
                        "icon-anchor": ["match", ["get", "type"], "highlight", "bottom", "center"],
                        # Highlight pins carry their own always-visible label.
                        "text-field": ["match", ["get", "type"], "highlight", ["get", "name"], ""],
                        "text-font": ["DIN Pro Bold", "Arial Unicode MS Bold"],
                        "text-size": 15, "text-anchor": "top", "text-offset": [0, 0.3],
                        "text-allow-overlap": True, "text-ignore-placement": True,
                        "symbol-z-elevate": False},
             "paint": {"symbol-z-offset": 3.6, "text-color": "#4264fb",
                       "text-halo-color": "#ffffff", "text-halo-width": 1.5}},
        ],
    }


assets = Path(__file__).resolve().parent.parent / "assets" / "indoor"
for name, native in [("citycube_fragment.json", True), ("citycube_fragment_config.json", False)]:
    (assets / name).write_text(json.dumps(build_fragment(native), indent=1) + "\n")
    print(f"wrote {assets / name} ({len(rooms)} rooms, {len(doors)} doors, {len(pois)} pois, native={native})")
