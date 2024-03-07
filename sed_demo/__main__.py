

from threading import Thread
import os
from dataclasses import dataclass
from typing import Optional

import torch
from omegaconf import OmegaConf

from sed_demo import AI4S_BANNER_PATH, SURREY_LOGO_PATH, CVSSP_LOGO_PATH, \
    EPSRC_LOGO_PATH, AUDIOSET_LABELS_PATH
from sed_demo.utils import load_csv_labels
from sed_demo.models import Cnn9_GMP_64x64
from sed_demo.audio_loop import AsynchAudioInputStream
from sed_demo.inference import AudioModelInference, PredictionTracker
from sed_demo.gui import DemoFrontend

from datetime import datetime, timedelta
import time
import json
import re
import time

from .tts import say

import pyttsx3

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, request, jsonify
from threading import Thread
from flask_cors import CORS


class DemoApp(DemoFrontend):
    BG_COLOR = "#fff8fa"
    BUTTON_COLOR = "#ffcc99"
    BAR_COLOR = "#ffcc99"
    tags = ['Explosion', 'Baby cry, infant cry', 'Smoke detector, smoke alarm']
    pval_threshold = 0.5
    email_sender = 'ai4sound.test@gmail.com'
    email_receiver = 'ai4sound.test@gmail.com'
    email_sender_pass = 'fazblwlyhermslps'
    state_file = 'state.json'
    def __init__(
            self,
            top_banner_path, logo_paths, model_path,
            all_labels, tracked_labels=None,
            samplerate=32000, audio_chunk_length=1024, ringbuffer_length=40000,
            model_winsize=1024, stft_hopsize=512, stft_window="hann",
            n_mels=64, mel_fmin=50, mel_fmax=14000,
            top_k=5, title_fontsize=22, table_fontsize=18):

        super().__init__(top_k, top_banner_path, logo_paths,
                         title_fontsize=title_fontsize,
                         table_fontsize=table_fontsize)
        self.audiostream = AsynchAudioInputStream(
            samplerate, audio_chunk_length, ringbuffer_length)
        num_audioset_classes = len(all_labels)
        self.model = Cnn9_GMP_64x64(num_audioset_classes)
        checkpoint = torch.load(model_path,
                                map_location=lambda storage, loc: storage)
        self.model.load_state_dict(checkpoint["model"])
        self.inference = AudioModelInference(
            self.model, model_winsize, stft_hopsize, samplerate, stft_window,
            n_mels, mel_fmin, mel_fmax)
        self.tracker = PredictionTracker(all_labels, allow_list=tracked_labels)
        self.top_k = top_k
        self.thread = None
        self.protocol("WM_DELETE_WINDOW", self.exit_demo)
        self.last_email_sent = datetime.min
    
            
    def process_and_save_data(self, value):
        time_pattern = r'\d{2}:\d{2}:\d{2}\.\d{3}'
        data_pattern = r'\(\'(.+?)\',\s(.+?)\)'
        timestamp = re.search(time_pattern, value).group()
        data_list = re.findall(data_pattern, value)
        data = {
            'timestamp': timestamp,
            'sounds': [{ 'label': label, 'confidence': float(confidence)} for label, confidence in data_list]
        }
        file_path = '/var/www/html/sound_datalog.json'
        short_file_path = '/var/www/html/sound_datalog_short.json'
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                if content:
                    json_data = json.loads(content)
                else:
                    json_data = []
        else:
            json_data = []
        json_data.append(data)
        with open(file_path, 'w') as file:
            file.write(json.dumps(json_data, ensure_ascii=False))
        short_data = json_data[-120:]  # Obtener los últimos 120 registros
        with open(short_file_path, 'w') as file:
            json.dump(short_data, file, ensure_ascii=False)

    def send_email(self, subject, message, from_addr, to_addr, from_password):
        try:
            msg = MIMEMultipart()
            msg['From'] = from_addr
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_addr, from_password)
            text = msg.as_string()
            server.sendmail(from_addr, to_addr, text)
            server.quit()
            print("Email sent successfully to " + to_addr)
        except smtplib.SMTPException as e:
            print(f"Failed to send email: {e}")

    def inference_loop(self):
        file_path = '/var/www/html/sound_datalog.json'
        while self.is_running():
            dl_inference = self.inference(self.audiostream.read())
            top_preds = self.tracker(dl_inference, self.top_k)
            for label, bar, (clsname, pval) in zip(
                    self.sound_labels, self.confidence_bars, top_preds):
                label["text"] = clsname
                bar["value"] = pval
                if (clsname in self.tags) and pval > self.pval_threshold:
                    print(clsname + ' Detected')
                    if datetime.now() - self.last_email_sent > timedelta(seconds=30):
                        self.send_email(
                            clsname + ' Detected', 
                            'A ' + clsname + ' has been detected with confidence ' + str(pval),
                            self.email_sender,
                            self.email_receiver,
                            self.email_sender_pass
                        )
                        self.last_email_sent = datetime.now()
                
            dataframe = datetime.now().strftime("%H:%M:%S.%f")[:-3] + str(top_preds)
            self.process_and_save_data(dataframe)
    
    def start(self):
        self.audiostream.start()
        self.thread = Thread(target=self.inference_loop)
        self.thread.daemon = True
        self.thread.start()  # will end automatically if is_running=False
        with open(self.state_file, 'w') as f:
            json.dump({'state': 'stop'}, f)
            print("state.json was opened")

    def stop(self):
        self.audiostream.stop()
        with open(self.state_file, 'w') as f:
            json.dump({'state': 'start'}, f)

    def exit_demo(self):
        if self.is_running():
            print("Waiting for threads to finish...")
            self.toggle_start()
        self.after(0, self.terminate_after_thread)

    def terminate_after_thread(self, wait_loop_ms=50):
        if self.thread is not None and self.thread.is_alive():
            self.after(wait_loop_ms, self.terminate_after_thread)
        else:
            print("Exiting...")
            self.audiostream.terminate()
            self.destroy()

@dataclass
class ConfDef:
    ALL_LABELS_PATH: str = AUDIOSET_LABELS_PATH
    SUBSET_LABELS_PATH: Optional[str] = None
    MODEL_PATH: str = os.path.join(
        "models", "Cnn9_GMP_64x64_300000_iterations_mAP=0.37.pth")
    SAMPLERATE: int = 32000
    AUDIO_CHUNK_LENGTH: int = 1024
    RINGBUFFER_LENGTH: int = int(32000 * 2)
    MODEL_WINSIZE: int = 1024
    STFT_HOPSIZE: int = 512
    STFT_WINDOW: str = "hann"
    N_MELS: int = 64
    MEL_FMIN: int = 50
    MEL_FMAX: int = 14000
    TOP_K: int = 6
    TITLE_FONTSIZE: int = 28
    TABLE_FONTSIZE: int = 22
    

app = Flask(__name__)
CORS(app)

file_path = '/var/www/html/sound_datalog.json'
CONF = OmegaConf.structured(ConfDef())
cli_conf = OmegaConf.from_cli()
CONF = OmegaConf.merge(CONF, cli_conf)
print("\n\nCONFIGURATION:")
print(OmegaConf.to_yaml(CONF), end="\n\n\n")

_, _, all_labels = load_csv_labels(CONF.ALL_LABELS_PATH)
if CONF.SUBSET_LABELS_PATH is None:
    subset_labels = None
else:
    _, _, subset_labels = load_csv_labels(CONF.SUBSET_LABELS_PATH)
logo_paths = [SURREY_LOGO_PATH, CVSSP_LOGO_PATH, EPSRC_LOGO_PATH]

demo = DemoApp(
    AI4S_BANNER_PATH, logo_paths, CONF.MODEL_PATH,
    all_labels, subset_labels,
    CONF.SAMPLERATE, CONF.AUDIO_CHUNK_LENGTH, CONF.RINGBUFFER_LENGTH,
    CONF.MODEL_WINSIZE, CONF.STFT_HOPSIZE, CONF.STFT_WINDOW,
    CONF.N_MELS, CONF.MEL_FMIN, CONF.MEL_FMAX,
    CONF.TOP_K, CONF.TITLE_FONTSIZE, CONF.TABLE_FONTSIZE)   
    
if os.path.exists(file_path):
    os.remove(file_path)

@app.route('/toggle', methods=['POST'])
def toggle():
    demo.dispatch_start()
    return 'Stop' if demo.is_running() else 'Start'

@app.route('/get_config', methods=['GET'])
def get_config():
    config = {
        'email_receiver': demo.email_receiver,
        'tags': demo.tags,
        'pval_threshold': demo.pval_threshold,
        # 'email_sender': demo.email_sender,
        # 'email_sender_pass': demo.email_sender_pass,
    }
    print(config)
    return jsonify(config)

@app.route('/update_config', methods=['POST'])
def update_config():
    # Aquí actualizarías las variables basándote en la solicitud
    # Por ahora, solo imprimiré los datos recibidos
    data = request.json
    demo.email_receiver = data.get('emailReceiver', demo.email_receiver)
    demo.tags = data.get('tags', demo.tags)
    demo.pval_threshold = data.get('pvalThreshold', demo.pval_threshold)
    # demo.email_sender = data.get('emailSender', demo.email_sender)
    # demo.email_sender_pass = data.get('emailPass', demo.email_sender_pass)
    with open('config.json', 'w') as f:
        json.dump(data, f, indent=4)
    return jsonify({"message": "Configuration updated successfully"}), 200

def run_flask_app():
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    
    Thread(target=run_flask_app).start()
    
    demo.mainloop()
