import threading
from give_away import send_full_data, send_small_data
from flask import Flask
import settings

app = Flask(__name__)

@app.route('/small_raport', methods=['POST'])
def small_raport():
    raport = threading.Thread(target=send_small_data)
    raport.daemon = True
    raport.start()

@app.route('/full_raport', methods=['POST'])
def full_raport():
    raport = threading.Thread(target=send_full_data)
    raport.daemon = True
    raport.start()

if __name__ == "__main__":

    app.run(host=settings.host, port=settings.port)
    #send_full_data()
    #send_small_data()