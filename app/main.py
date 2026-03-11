from __future__ import annotations

import logging
import signal
import sys
from pathlib import Path

from flask import Flask, jsonify

from app.config import Settings
from app.consumer import OCRConsumer

settings = Settings.from_env()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(settings.app_name)
Path(settings.tmp_dir).mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
consumer = OCRConsumer(settings)


@app.get("/actuator/health/liveness")
def liveness():
    return jsonify({"status": "UP", "service": settings.app_name})


@app.get("/actuator/health/readiness")
def readiness():
    healthy = consumer.ready and consumer.is_alive()
    status = "UP" if healthy else "OUT_OF_SERVICE"
    code = 200 if healthy else 503
    return jsonify({"status": status, "service": settings.app_name}), code


@app.get("/actuator/health")
def health():
    healthy = consumer.ready and consumer.is_alive()
    status = "UP" if healthy else "OUT_OF_SERVICE"
    code = 200 if healthy else 503
    return jsonify({"status": status, "components": {"consumer": {"status": status}}}), code


def _shutdown(*_: object) -> None:
    logger.info("Encerrando %s", settings.app_name)
    consumer.stop()
    sys.exit(0)


def main() -> None:
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    consumer.start()
    app.run(host="0.0.0.0", port=settings.server_port)


if __name__ == "__main__":
    main()
