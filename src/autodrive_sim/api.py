"""Local HTTP API for running the Python simulator from the web dashboard.

Start from the repository root with:
    $env:PYTHONPATH = "src"
    python -m autodrive_sim.api
"""

from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import statistics
from urllib.parse import urlparse

from autodrive_sim.benchmark import SCENARIOS, run_episode


HOST = "127.0.0.1"
PORT = 8000
CONTROLLERS = {"baseline", "safety", "steering"}
ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}


def run_benchmark(controller: str, scenario: str, episodes: int) -> dict:
    """Run repeatable episodes and return the same metrics as the CLI."""
    results = [
        run_episode(controller_name=controller, scenario_name=scenario)
        for _ in range(episodes)
    ]
    lane_values = [
        float(result["lane_deviation_mean_m"])
        for result in results
        if result["lane_deviation_mean_m"] is not None
    ]
    return {
        "controller": controller,
        "scenario": scenario,
        "simulator": "lightweight_2d",
        "episode_count": len(results),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "aggregate": {
            "mean_lane_deviation_m": (
                statistics.mean(lane_values) if lane_values else None
            ),
            "mean_collision_events": statistics.mean(
                int(result["collision_events"]) for result in results
            ),
            "mean_route_completion_pct": statistics.mean(
                float(result["route_completion_pct"]) for result in results
            ),
            "safe_stop_rate": statistics.mean(
                int(result["stopped_before_route"]) for result in results
            ),
        },
        "episodes": results,
        "notes": [
            "Results are from the deterministic lightweight 2D simulator.",
            "These results are not CARLA results or trained neural-network results.",
            "Steering MAE requires expert steering labels.",
        ],
    }


def run_controller_comparison(scenario: str, episodes: int) -> dict:
    """Evaluate all controllers on the same deterministic scenario."""
    reports = [run_benchmark(name, scenario, episodes) for name in ("baseline", "safety", "steering")]
    return {
        "scenario": scenario,
        "simulator": "lightweight_2d",
        "episode_count_per_controller": episodes,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reports": reports,
        "interpretation": "Compare collision and route-completion trade-offs. Repeated deterministic episodes assess consistency, not independent randomized trials.",
    }


class SimulatorAPIHandler(BaseHTTPRequestHandler):
    """Small standard-library API intended for local dashboard development."""

    server_version = "AutonomyLabAPI/0.1"

    def _send_json(self, status: HTTPStatus, payload: dict) -> None:
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        origin = self.headers.get("Origin", "")
        self.send_response(status)
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send_json(HTTPStatus.NO_CONTENT, {})

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {"status": "ok", "service": "python-simulator", "simulator": "lightweight_2d"},
            )
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path not in {"/api/benchmark", "/api/compare"}:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found."})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 16_384:
                raise ValueError("Request body must be between 1 and 16384 bytes.")
            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object.")

            controller = payload.get("controller", "steering")
            scenario = payload.get("scenario", "center")
            episodes = payload.get("episodes", 1)
            if path == "/api/benchmark" and (not isinstance(controller, str) or controller not in CONTROLLERS):
                raise ValueError("Choose baseline, safety, or steering controller.")
            if not isinstance(scenario, str) or scenario not in SCENARIOS:
                raise ValueError(f"Choose one of these scenarios: {', '.join(SCENARIOS)}.")
            maximum = 25 if path == "/api/compare" else 100
            if isinstance(episodes, bool) or not isinstance(episodes, int) or not 1 <= episodes <= maximum:
                raise ValueError(f"episodes must be a whole number from 1 to {maximum}.")

            report = (run_controller_comparison(scenario, episodes) if path == "/api/compare"
                      else run_benchmark(controller, scenario, episodes))
            self._send_json(HTTPStatus.OK, {"status": "completed", "report": report})
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Request body must contain valid JSON."})
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except Exception:
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Benchmark execution failed."})

    def log_message(self, format: str, *args) -> None:
        print(f"[simulator-api] {self.address_string()} - {format % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), SimulatorAPIHandler)
    print(f"Python simulator API listening at http://{HOST}:{PORT}")
    print("Health check: http://127.0.0.1:8000/api/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping simulator API...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
