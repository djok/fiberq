"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { cn } from "@/lib/utils";
import { useTranslations } from "next-intl";

interface ProjectMiniMapProps {
  extent: GeoJSON.Geometry | null;
  className?: string;
}

/**
 * Compute bounding box from GeoJSON geometry coordinates.
 */
function getBounds(
  geometry: GeoJSON.Geometry,
): [[number, number], [number, number]] {
  const coords: number[][] = [];

  function extractCoords(g: GeoJSON.Geometry) {
    switch (g.type) {
      case "Point":
        coords.push(g.coordinates as number[]);
        break;
      case "MultiPoint":
      case "LineString":
        (g.coordinates as number[][]).forEach((c) => coords.push(c));
        break;
      case "MultiLineString":
      case "Polygon":
        (g.coordinates as number[][][]).forEach((ring) =>
          ring.forEach((c) => coords.push(c)),
        );
        break;
      case "MultiPolygon":
        (g.coordinates as number[][][][]).forEach((poly) =>
          poly.forEach((ring) => ring.forEach((c) => coords.push(c))),
        );
        break;
      case "GeometryCollection":
        g.geometries.forEach(extractCoords);
        break;
    }
  }

  extractCoords(geometry);

  if (coords.length === 0) {
    return [
      [0, 0],
      [0, 0],
    ];
  }

  let minLng = Infinity,
    minLat = Infinity,
    maxLng = -Infinity,
    maxLat = -Infinity;
  for (const c of coords) {
    if (c[0] < minLng) minLng = c[0];
    if (c[1] < minLat) minLat = c[1];
    if (c[0] > maxLng) maxLng = c[0];
    if (c[1] > maxLat) maxLat = c[1];
  }

  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}

export function ProjectMiniMap({ extent, className }: ProjectMiniMapProps) {
  const t = useTranslations("projects");
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [isVisible, setIsVisible] = useState(false);

  // Intersection Observer for lazy loading
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { rootMargin: "100px" },
    );

    observer.observe(container);
    return () => observer.disconnect();
  }, []);

  // Create map when visible and extent exists
  useEffect(() => {
    if (!isVisible || !extent || !containerRef.current) return;
    if (mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: "raster",
            tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
            tileSize: 256,
            attribution: "&copy; OpenStreetMap contributors",
          },
        },
        layers: [
          {
            id: "osm-tiles",
            type: "raster",
            source: "osm",
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      interactive: false,
      attributionControl: false,
    });

    mapRef.current = map;

    map.on("load", () => {
      const geojson: GeoJSON.Feature = {
        type: "Feature",
        geometry: extent,
        properties: {},
      };

      map.addSource("extent", {
        type: "geojson",
        data: geojson,
      });

      map.addLayer({
        id: "extent-fill",
        type: "fill",
        source: "extent",
        paint: {
          "fill-color": "#0d9488",
          "fill-opacity": 0.15,
        },
      });

      map.addLayer({
        id: "extent-line",
        type: "line",
        source: "extent",
        paint: {
          "line-color": "#0d9488",
          "line-width": 2,
        },
      });

      const bounds = getBounds(extent);
      map.fitBounds(bounds, { padding: 20, animate: false });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [isVisible, extent]);

  if (!extent) {
    return (
      <div
        className={cn(
          "flex items-center justify-center bg-muted text-xs text-muted-foreground",
          className,
        )}
      >
        {t("noGeographicData")}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={cn("bg-muted", className)}
    />
  );
}
