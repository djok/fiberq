#!/usr/bin/env python3
"""
FiberQ QField Project Generator

Generates a QField-ready .qgz project from a PostGIS database or
from the FiberQ API server. The generated project includes:
- All infrastructure layers with QML styles
- SVG map icons bundled in the project
- Custom .ui forms for field data entry
- OSM basemap
- Offline-ready structure

Usage:
    python generate_qfield_project.py --config ../fiberq/config.ini --output ./qfield_project
    python generate_qfield_project.py --server https://fiberq.company.com --token <jwt> --project-id 1

Requirements:
    pip install qgis  (or run from QGIS Python console)
"""

import argparse
import configparser
import os
import shutil
import sys


def _load_config(config_path: str) -> dict:
    cp = configparser.ConfigParser()
    cp.read(config_path, encoding="utf-8")

    pg = cp["postgis"] if "postgis" in cp else {}
    layers = cp["layers"] if "layers" in cp else {}
    basemaps = cp["basemaps"] if "basemaps" in cp else {}

    return {
        "pg": {
            "host": pg.get("host", "localhost").strip(),
            "port": pg.get("port", "5433").strip(),
            "dbname": pg.get("dbname", "gis").strip(),
            "user": pg.get("user", "").strip(),
            "password": pg.get("password", "").strip(),
            "schema": pg.get("schema", "fiberq").strip(),
            "sslmode": pg.get("sslmode", "disable").strip(),
        },
        "layers": dict(layers),
        "basemaps": {
            "osm_url": basemaps.get("osm_url", "https://tile.openstreetmap.org/{z}/{x}/{y}.png").strip(),
        },
    }


# Layer definitions: (table_name, geom_type, layer_name, qml_style_file)
LAYER_DEFS = [
    ("ftth_trase",             "LineString",   "Route",              "Route.qml"),
    ("ftth_stubovi",           "Point",        "Poles",              "Poles.qml"),
    ("ftth_okna",              "Point",        "Manholes",           "Manholes.qml"),
    ("ftth_kablovi_podzemni",  "LineString",   "Underground cables", "Underground cables.qml"),
    ("ftth_kablovi_nadzemni",  "LineString",   "Aerial cables",      "Aerial cables.qml"),
    ("ftth_cevi",              "LineString",   "PE pipes",           "PE pipes.qml"),
    ("ftth_mufovi",            "Point",        "Joint Closures",     "Joint Closures.qml"),
    ("ftth_spojevi",           "Point",        "Fiber break",        "Fiber break.qml"),
    ("ftth_elements",          "Point",        "Elements",           "ODF.qml"),
    # New tables for server sync
    ("fiber_splice_closures",  "Point",        "Splice Closures",    None),
    ("work_orders",            "Polygon",      "Work Orders",        None),
    ("smr_reports",            "Point",        "SMR Reports",        None),
    ("field_photos",           "Point",        "Field Photos",       None),
]

# .ui form assignments
FORM_ASSIGNMENTS = {
    "Poles":              "poles.ui",
    "Manholes":           "manholes.ui",
    "Underground cables": "cables_underground.ui",
    "Aerial cables":      "cables_aerial.ui",
    "Route":              "routes.ui",
    "Elements":           "elements.ui",
    "Fiber break":        "fiber_break.ui",
    "Splice Closures":    "splice_record.ui",
    "SMR Reports":        "smr_report.ui",
    "Work Orders":        "work_order_view.ui",
}


def generate_project(config: dict, output_dir: str, project_name: str = "FiberQ Field"):
    """
    Generate a QField-ready project directory structure.

    This function creates:
    - {output_dir}/
      ├── {project_name}.qgs   (QGIS project file)
      ├── styles/               (QML style files)
      ├── icons/                (SVG map icons)
      ├── forms/                (custom .ui forms)
      └── data/                 (offline data if needed)
    """
    try:
        from qgis.core import (
            QgsApplication, QgsProject, QgsVectorLayer,
            QgsDataSourceUri, QgsCoordinateReferenceSystem,
            QgsRasterLayer, QgsEditFormConfig
        )
    except ImportError:
        print("ERROR: QGIS Python bindings not available.")
        print("Run this script from the QGIS Python console or ensure PyQGIS is in your path.")
        sys.exit(1)

    # Initialize QGIS if not already running
    app = QgsApplication.instance()
    standalone = False
    if app is None:
        app = QgsApplication([], False)
        app.initQgis()
        standalone = True

    try:
        _do_generate(config, output_dir, project_name)
    finally:
        if standalone:
            app.exitQgis()


def _do_generate(config: dict, output_dir: str, project_name: str):
    from qgis.core import (
        QgsProject, QgsVectorLayer, QgsDataSourceUri,
        QgsCoordinateReferenceSystem, QgsRasterLayer,
        QgsEditFormConfig
    )

    # Create output directory structure
    os.makedirs(output_dir, exist_ok=True)
    styles_dir = os.path.join(output_dir, "styles")
    icons_dir = os.path.join(output_dir, "icons")
    forms_dir = os.path.join(output_dir, "forms")
    data_dir = os.path.join(output_dir, "data")
    os.makedirs(styles_dir, exist_ok=True)
    os.makedirs(icons_dir, exist_ok=True)
    os.makedirs(forms_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # Copy styles and icons from plugin directory
    plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fiberq")
    src_styles = os.path.join(plugin_dir, "styles")
    src_icons = os.path.join(plugin_dir, "resources", "map_icons")
    src_forms = os.path.join(os.path.dirname(__file__), "qfield_forms")

    if os.path.isdir(src_styles):
        for f in os.listdir(src_styles):
            if f.endswith(".qml"):
                shutil.copy2(os.path.join(src_styles, f), styles_dir)

    if os.path.isdir(src_icons):
        for f in os.listdir(src_icons):
            if f.endswith(".svg"):
                shutil.copy2(os.path.join(src_icons, f), icons_dir)

    if os.path.isdir(src_forms):
        for f in os.listdir(src_forms):
            if f.endswith(".ui"):
                shutil.copy2(os.path.join(src_forms, f), forms_dir)

    # Create QGIS project
    project = QgsProject.instance()
    project.clear()
    project.setTitle(project_name)

    crs = QgsCoordinateReferenceSystem("EPSG:4326")
    project.setCrs(crs)

    pg = config["pg"]

    # Add PostGIS layers
    for table, geom_type, layer_name, qml_file in LAYER_DEFS:
        uri = QgsDataSourceUri()
        uri.setConnection(pg["host"], pg["port"], pg["dbname"],
                          pg["user"], pg["password"],
                          QgsDataSourceUri.SslMode(0))  # disable
        uri.setDataSource(pg["schema"], table, "geom", "", "id")

        layer = QgsVectorLayer(uri.uri(False), layer_name, "postgres")
        if not layer.isValid():
            print(f"  WARNING: Layer '{layer_name}' ({table}) is not valid, skipping.")
            continue

        # Apply QML style
        if qml_file:
            qml_path = os.path.join(styles_dir, qml_file)
            if os.path.exists(qml_path):
                layer.loadNamedStyle(qml_path)

        # Apply .ui form
        form_file = FORM_ASSIGNMENTS.get(layer_name)
        if form_file:
            form_path = os.path.join(forms_dir, form_file)
            if os.path.exists(form_path):
                config_form = layer.editFormConfig()
                config_form.setUiForm(form_path)
                config_form.setLayout(QgsEditFormConfig.UiFileLayout)
                layer.setEditFormConfig(config_form)

        project.addMapLayer(layer)
        print(f"  Added layer: {layer_name}")

    # Add OSM basemap
    osm_url = config["basemaps"]["osm_url"]
    if osm_url:
        osm_uri = (
            f"type=xyz&url={osm_url}"
            f"&zmin=0&zmax=19"
        )
        osm_layer = QgsRasterLayer(osm_uri, "OpenStreetMap", "wms")
        if osm_layer.isValid():
            project.addMapLayer(osm_layer)
            print("  Added basemap: OpenStreetMap")

    # Save project
    project_path = os.path.join(output_dir, f"{project_name}.qgs")
    project.write(project_path)
    print(f"\nProject saved to: {project_path}")
    print(f"Output directory: {output_dir}")
    print("\nTo use with QField:")
    print(f"  1. Copy the entire '{os.path.basename(output_dir)}' folder to your device")
    print(f"  2. Open '{project_name}.qgs' in QField")
    print("  3. All styles, icons, and forms should load automatically")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a QField-ready project from FiberQ PostGIS database"
    )
    parser.add_argument(
        "--config", "-c",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)),
                             "fiberq", "config.ini"),
        help="Path to FiberQ config.ini"
    )
    parser.add_argument(
        "--output", "-o",
        default="./qfield_project",
        help="Output directory for the QField project"
    )
    parser.add_argument(
        "--name", "-n",
        default="FiberQ Field",
        help="Project name"
    )

    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"ERROR: Config file not found: {args.config}")
        sys.exit(1)

    config = _load_config(args.config)
    print(f"Generating QField project from: {args.config}")
    print(f"PostGIS: {config['pg']['host']}:{config['pg']['port']}/{config['pg']['dbname']}")
    print(f"Schema: {config['pg']['schema']}")
    print()

    generate_project(config, args.output, args.name)


if __name__ == "__main__":
    main()
