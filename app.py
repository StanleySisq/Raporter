from give_away import send_full_data, send_small_data
from flask import Flask
import settings

app = Flask(__name__)

@app.route('/small_raport', methods=['POST'])
def small_raport():
    send_full_data()

@app.route('/full_raport', methods=['POST'])
def full_raport():
    send_small_data()

if __name__ == "__main__":

    app.run(host=settings.host, port=settings.port)
    #send_full_data()
    #send_small_data()