"use client";

import { CircleMarker, MapContainer, TileLayer, Tooltip } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export function IocIpMap({
  lat,
  lng,
  label,
}: {
  lat: number;
  lng: number;
  label: string;
}) {
  return (
    <MapContainer
      center={[lat, lng]}
      zoom={4}
      className="z-0 h-64 w-full rounded-xl"
      scrollWheelZoom={false}
      attributionControl
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <CircleMarker
        center={[lat, lng]}
        radius={12}
        pathOptions={{
          color: "#22d3ee",
          fillColor: "#ff2d55",
          fillOpacity: 0.35,
          weight: 2,
        }}
      >
        <Tooltip direction="top" offset={[0, -8]} opacity={1} permanent={false}>
          {label}
        </Tooltip>
      </CircleMarker>
    </MapContainer>
  );
}
