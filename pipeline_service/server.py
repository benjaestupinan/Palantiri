import base64
import json
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, request, jsonify

from pipeline_service.pipeline import Pipeline
from pipeline_service.tts import synthesize

app = Flask(__name__)
_pipeline = Pipeline()

_feedback_handler = RotatingFileHandler("logs/pipeline.log", maxBytes=1_000_000_000, backupCount=3)
_feedback_logger = logging.getLogger("feedback")
_feedback_logger.addHandler(_feedback_handler)
_feedback_logger.setLevel(logging.INFO)


@app.post("/message")
def message():
    body = request.get_json()
    session_id = body.get("session_id")
    user_msg = body["message"]

    session_id, text, flow_id = _pipeline.process_message(session_id, user_msg)
    audio_bytes = synthesize(text)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return jsonify({"session_id": session_id, "text": text, "audio": audio_b64, "flow_id": flow_id})


@app.post("/feedback")
def feedback():
    body = request.get_json()
    _feedback_logger.info(json.dumps({"flow_id": body["flow_id"], "ok": body["ok"]}, ensure_ascii=False))
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8084)
