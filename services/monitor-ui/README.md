# CSMP Monitor UI (Phase 6)

Leaflet map consuming the Monitor API. Served at **http://127.0.0.1:8000/app/** when
`monitor-api` is running (static files mounted by FastAPI).

## Features

- OpenStreetMap + Leaflet markers per intersection
- pt-BR labels (signal states, health, gargalo filter)
- Bottleneck highlights (pulsing red markers + sidebar tag)
- Auto-refresh every 30 seconds

## Run

```powershell
.\Makefile.ps1 demo          # optional: load data
.\Makefile.ps1 monitor-api   # open http://127.0.0.1:8000/app/
```

No separate build step — plain HTML/CSS/JS in `static/`.
