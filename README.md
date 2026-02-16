# Weighing Scale API

Simple FastAPI service that reads weight values from a serial-connected scale and exposes them over HTTP.

## Features

- Reads live weight from a serial port (`pyserial`).
- Exposes latest weight via REST endpoint.
- Provides health endpoint with connection/runtime diagnostics.
- Handles reconnect attempts when the serial device is unavailable.
- Configurable via environment variables.

## Project Structure

- `api.py`: FastAPI app, CORS settings, startup/shutdown lifecycle, API models/endpoints.
- `scale_reader.py`: Serial communication logic, parsing, retries, thread-safe latest state.
- `requirements.txt`: Python dependencies.
- `.env.example`: Sample environment configuration.
- `api.bat`: Windows helper to run uvicorn.

## Requirements

- Python 3.10+

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

The service is configured by environment variables:

| Variable | Default | Description |
|---|---|---|
| `SCALE_PORT` | `COM5` | Serial port where scale is connected |
| `SCALE_BAUDRATE` | `9600` | Serial baudrate |
| `SCALE_TIMEOUT` | `1` | Serial read timeout (seconds) |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |

### Quick setup

```bash
cp .env.example .env
# then edit values as needed
```

### Example

```bash
export SCALE_PORT=COM5
export SCALE_BAUDRATE=9600
export SCALE_TIMEOUT=1
export CORS_ORIGINS=http://localhost:3000,https://your-odoo-domain.com
```

## Run the Service

### Linux/macOS

```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Windows

```bat
api.bat
```

## API Endpoints

### `GET /api/weight`

Returns the latest parsed scale reading.

#### Success response

```json
{
  "weight": 12.45,
  "unit": "kg",
  "timestamp": "2026-02-16T10:20:30.123456Z"
}
```

#### Pending response (no reading yet)

```json
{
  "error": "No data yet."
}
```

### `GET /api/health`

Returns process/runtime state.

#### Example response

```json
{
  "status": "ok",
  "running": true,
  "serial_connected": false,
  "port": "COM5",
  "last_timestamp": null,
  "last_error": "Failed to connect: ..."
}
```

## Operational Notes

- `last_error` is useful for troubleshooting hardware/port issues without opening logs.
- The reader thread starts with application startup and stops on shutdown.
- If serial connection drops, the reader retries in the background.

## Troubleshooting

### `ModuleNotFoundError: No module named 'serial'`

Install dependencies:

```bash
pip install -r requirements.txt
```

### No data returned from `/api/weight`

- Confirm the scale is connected to the configured `SCALE_PORT`.
- Verify baudrate and serial settings match the scale.
- Check `/api/health` for `serial_connected` and `last_error`.

### CORS issues from frontend/Odoo

Set explicit origins in `CORS_ORIGINS` (comma-separated) instead of wildcard.

## Security & Deployment Recommendations

- Restrict `CORS_ORIGINS` to known frontend domains in production.
- Run behind reverse proxy (Nginx/Caddy) with HTTPS.
- Collect logs centrally for device diagnostics.
