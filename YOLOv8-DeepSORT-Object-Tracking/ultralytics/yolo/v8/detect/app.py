from flask import Flask, render_template, request, jsonify, after_this_request, send_file, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import os
import subprocess
from glob import glob
from tkinter import filedialog, messagebox
import shutil

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


with app.app_context():
    db.create_all()

UPLOAD_FOLDER = 'C:\\Users\\91939\\OneDrive\\Desktop\\MajorProject\\YOLOv8-DeepSORT-Object-Tracking\\ultralytics\\yolo\\v8\\detect'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

latest_video_name = ""

def get_latest_video():
    videos = glob(os.path.join(app.config['UPLOAD_FOLDER'], '*.mp4'))
    if videos:
        return max(videos, key=os.path.getctime)
    return None

def get_output_video_path():
    runs_folder = "C:\\Users\\91939\\OneDrive\\Desktop\\MajorProject\\YOLOv8-DeepSORT-Object-Tracking\\runs\\detect"
    latest_folder = max(glob(os.path.join(runs_folder, '*/')), key=os.path.getctime)
    video_file = os.path.join(latest_folder, latest_video_name)
    return video_file

def upload_video():
    global latest_video_name
    file_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4")])
    if file_path:
        video_name = os.path.basename(file_path)

        destination_path = os.path.join(app.config['UPLOAD_FOLDER'], video_name)
        shutil.copy2(file_path, destination_path)
        latest_video_name = video_name
        messagebox.showinfo("Video Uploaded", "Video uploaded successfully.")
        print("Video uploaded successfully.")

@app.route('/')
def index():
    return render_template('login.html')


@app.route('/users', methods=['GET'])
def view_users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']


        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return render_template('register.html', error='Email already exists...')

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')



@app.route('/dashboard')
def dashboard():
    if session['email']:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('dashboard.html', user=user)

    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        if not filename.endswith('.mp4'):
            filename += '.mp4'
        file.save(filename)

        global latest_video_name
        latest_video_name = file.filename

        return jsonify({'message': 'Video uploaded successfully'}), 200

@app.route('/process', methods=['GET'])
def process():
    global latest_video_name
    if latest_video_name:
        command = [
            'python',
            'C:\\Users\\91939\\OneDrive\\Desktop\\MajorProject\\YOLOv8-DeepSORT-Object-Tracking\\ultralytics\\yolo\\v8\\detect\\predict.py'
        ]
        arguments = [f'source={latest_video_name}', 'model=yolov8x.pt', 'show=True']
        try:
            subprocess.run(command + arguments, check=True)
            return jsonify({'message': 'Video processed successfully'}), 200
        except subprocess.CalledProcessError as e:
            return jsonify({'message': f'Error during video processing: {e}'}), 500
    else:
        return jsonify({'message': 'No video to process'}), 400

@app.route('/download', methods=['GET'])
def download():
    try:
        video_file = get_output_video_path()
        return send_file(video_file, as_attachment=True)
    except Exception as e:
        return jsonify({'message': f'Error during download: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
