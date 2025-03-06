from flask import Flask, jsonify
import threading
from give_away import send_full_data, send_small_data
from live_report_data import send_live_data
import settings, db_funcs
from users_maintai import put_new_user_in_groups

app = Flask(__name__)

def run_in_background(target):

    thread = threading.Thread(target=target)
    thread.daemon = True  
    thread.start()

@app.route('/small_raport', methods=['POST'])
def small_raport():

    run_in_background(send_small_data) 
    return jsonify({
        "task_id": "small_report_task",
        "message": "Task accepted and is being processed."
    }), 202

@app.route('/full_raport', methods=['POST'])
def full_raport():

    run_in_background(send_full_data) 
    return jsonify({
        "task_id": "full_report_task",
        "message": "Task accepted and is being processed."
    }), 202

@app.route('/update_groups', methods=['POST'])
def update_groups():

    run_in_background(put_new_user_in_groups) 
    return jsonify({
        "task_id": "full_report_task",
        "message": "Task accepted and is being processed."
    }), 202

@app.route('/live_raport', methods=['POST'])
def update_groups():

    run_in_background(send_live_data) 
    return jsonify({
        "task_id": "live_report_task",
        "message": "Task accepted and is being processed."
    }), 202

if __name__ == "__main__":
    db_funcs.init_database()
    app.run(host=settings.host, port=settings.port)