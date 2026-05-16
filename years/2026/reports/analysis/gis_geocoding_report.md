# GIS Geocoding Report

Generated: 2026-05-17

## Purpose

This report records how event venue/studio addresses were converted into latitude/longitude coordinates for the 2026 Yeonhui Yoga Week GIS analysis.

## Inputs

- Location seed table: `data/external/studio_locations_public.csv`
- Address source: ON STUDIO class descriptions

## Method

- Geocoder: ArcGIS World Geocoding Service
- Endpoint: `https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates`
- Query unit: one unique address string per venue/studio
- Confidence rule:
  - `needs_manual_verification=false` when the top candidate score is at least 95 and the address type is `PointAddress` or `StreetAddress`
  - otherwise `needs_manual_verification=true`

## Result

- Rows in location table: 16
- Rows with coordinates: 16
- Rows needing manual verification: 0

## Rows Needing Manual Verification

_No rows_
