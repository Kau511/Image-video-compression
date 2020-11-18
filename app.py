from flask import Flask, url_for, jsonify, request, send_file
import PIL
from PIL import Image 
import io
from config import config
import pyrebase
from moviepy.editor import *
from werkzeug.utils import secure_filename
from moviepy.video.fx.resize import resize
from datetime import datetime
import os
from flask_cors import CORS


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','mp4','avi','mov'}
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
UPLOAD_FOLDER = os.path.join("download")
COMPRESSED_FOLDER = os.path.join("compress")
logo_folder = os.path.join("logos")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['COMPRESS_FOLDER'] = COMPRESSED_FOLDER
app.config['logo_folder'] = logo_folder

def raw_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        print(filename)
        if filename.lower().endswith('.png'):
            img = Image.open(file)
            img1 = img.convert('P', palette=Image.ADAPTIVE)
            img_bytes = io.BytesIO()
            img1.save(img_bytes,'PNG',quality='low',optimze=True)
            img_bytes.seek(0)
            print("i am in PNG looop")
            mimetype = 'image/png'
            return img_bytes, mimetype
        else:
            if filename.lower().endswith(('.jpg','jpeg')):
                img = Image.open(file)
                width,height = img.size
                img_bytes = io.BytesIO()
                img1 = img.resize((width,height),PIL.Image.ANTIALIAS)
                img1.save(img_bytes,'JPEG',quality='web_low',optimze=True)
                img_bytes.seek(0)
                print("i am in Jpeg looop")
                mimetype = 'image/jpeg'
                return img_bytes, mimetype

def url_return(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        print(filename)
        if filename.lower().endswith('.png'):
            img = Image.open(file)
            img1 = img.convert('P', palette=Image.ADAPTIVE)
            img_bytes = io.BytesIO()
            img1.save(img_bytes,'PNG',quality='low',optimze=True)
            img_bytes.seek(0)
            print("i am in PNG looop")
        else:
            if filename.lower().endswith(('.jpg','jpeg')):
                img = Image.open(file)
                width,height = img.size
                img_bytes = io.BytesIO()
                img1 = img.resize((width,height),PIL.Image.ANTIALIAS)
                img1.save(img_bytes,'JPEG',quality='web_low',optimze=True)
                img_bytes.seek(0)
                print("i am in Jpeg looop")
        filename1 = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p") + '_' + filename  
        storage.child("compressed_images/" +str(filename1)).put(img_bytes)
        link = storage.child("compressed_images/" + str(filename1)).get_url(None)
    return (link)

@app.route('/', methods = ['GET','POST'])
def compress():
    try:
        if 'file' not in request.files and 'type' not in request.args:
            return('upload image to compress and enter response type')
        if 'file' in request.files and 'type' in request.args:
            file = request.files['file']
            responsetype = request.args['type']
            print(responsetype)
            if responsetype == 'raw':
                response, mimetype = raw_file(file)
                print(mimetype)
                return send_file(response, mimetype=mimetype)
            elif responsetype == 'string':
                response = url_return(file)
                return response
            else:
                response = url_return(file)
                return response
        return ("Error")
    except Exception as e:
        return (str(e))

@app.route('/video', methods = ['GET','POST'])
def video_compress():
    try:
        if 'file' not in request.files and 'superimpose_text' and 'superimpose_image' not in request.files:
            return ("upload video and imposing parameters")
        if 'file' in request.files and 'superimpose_text' in request.form and 'superimpose_image' in request.files:
            file = request.files['file']
            impose_text = request.form['superimpose_text']
            impose_logo = request.files['superimpose_image']

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename1 = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p") + "_" + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename1))
                # storage.child("videos/" +str(filename1)).put(file)
                # link = storage.child("videos/" + str(filename1)).get_url(None)
            path = (UPLOAD_FOLDER+"/"+filename1)
            clip = VideoFileClip(path)
            newsize = clip.size
            clip2 = resize(clip,(640,480))
            if len(impose_text) != 0:
                txt_clip = (TextClip(impose_text,fontsize=50,color='blue',font='Times-BoldItalic')
                      .set_position(('right','bottom')).set_duration(clip.duration).margin(right=8,top=8,bottom=8,opacity=0))
                result = CompositeVideoClip([clip2, txt_clip])
                #print(impose_text)
                result.write_videofile(os.path.join(COMPRESSED_FOLDER,filename1),codec="libx264")
                returnpath = "home/ubuntu/image-compression/compress/" + str(filename1)
            elif impose_logo != None:
                logofilename = secure_filename(impose_logo.filename)
                impose_logo.save(os.path.join(app.config['logo_folder'],logofilename))
                logopath = (logo_folder + "/" + logofilename)
                logo = (ImageClip(logopath).set_duration(clip.duration).set_position(("right","bottom"))
                    .resize(height=50,width=70).margin(right=8,top=8,bottom=8,opacity=0))
                result = CompositeVideoClip([clip2, logo])
                result.write_videofile(os.path.join(COMPRESSED_FOLDER,filename1),codec="libx264")
                returnpath = "/home/ubuntu/image-compression/compress/" + str(filename1)
            return (returnpath)
        return ("ERROR")
    except Exception as e:
        return (str(e))


if __name__ == "__main__":
    app.run(debug=True)
