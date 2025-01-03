from flask import Flask, jsonify
import threading
from give_away import send_full_data, send_small_data
import settings, db_funcs

app = Flask(__name__)

def run_in_background(target):
    """
    Helper function to run a task in a separate thread.
    """
    thread = threading.Thread(target=target)
    thread.daemon = True  # Daemon threads exit when the main program exits
    thread.start()

@app.route('/small_raport', methods=['POST'])
def small_raport():
    """
    Endpoint to trigger the generation of a small report.
    """
    run_in_background(send_small_data)  # Start task in the background
    return jsonify({
        "task_id": "small_report_task",
        "message": "Task accepted and is being processed."
    }), 202

@app.route('/full_raport', methods=['POST'])
def full_raport():
    """
    Endpoint to trigger the generation of a full report.
    """
    run_in_background(send_full_data)  # Start task in the background
    return jsonify({
        "task_id": "full_report_task",
        "message": "Task accepted and is being processed."
    }), 202

if __name__ == "__main__":
    db_funcs.init_database()
    app.run(host=settings.host, port=settings.port)