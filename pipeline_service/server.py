import base64

from flask import Flask, request, jsonify

from pipeline_service.pipeline import Pipeline
from pipeline_service.tts import synthesize

app = Flask(__name__)
_pipeline = Pipeline()


@app.post("/message")
def message():
    body = request.get_json()
    session_id = body.get("session_id")
    user_msg = body["message"]

    session_id, text = _pipeline.process_message(session_id, user_msg)
    audio_bytes = synthesize(text)
    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

    return jsonify({"session_id": session_id, "text": text, "audio": audio_b64})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8084)
