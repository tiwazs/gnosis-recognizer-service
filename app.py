from flask import Flask, Request, Response
import json, os, time
from uuid import uuid4
import encoder_extractor

# Some definitions
NET = None
METADATA = None
MAX_SIMULTANEOUS_PROCESSES = 1
NUM_SESSIONS = 0
HOST = "0.0.0.0"
PORT = "3000"


# Creating our server
app = Flask(__name__)

#======================================================Requests============================================================

# Creating our face detection and recognition sistem.
encoder = encoder_extractor.encoderExtractor(None)

@app.route('/load_models', methods=['GET'])
def load_models():
    print("load_models")
    return result

@app.route('/unload_models', methods=['GET'])
def unload_models():
    print("unload_models")
    return result

@app.route('/encode_images', methods=['POST'])
def encode_images():
    print("encode_images")
    return result

@app.route('/compare_to_dataset', methods=['POST'])
def compare_to_dataset():
    print("compare_to_dataset")
    return result

@app.route('/start_live_analytics', methods=['GET'])
def start_live_analytics():
    print("start_live_analytics")
    return result

@app.route('/stop_live_analytics', methods=['GET'])
def stop_live_analytics():
    print("stop_live_analytics")
    return result

if __name__=="__main__":
    print(MAX_SIMULTANEOUS_PROCESSES)

    app.run(host=HOST, port=PORT)