import os
import Transform
from flask import Flask, request , send_from_directory , send_file,render_template
from flask_uploads import UploadSet, configure_uploads, IMAGES,\
 patch_request_class
from werkzeug import secure_filename
#coding:utf-8
#from flask.ext.bootstrap import Bootstrap #专为Flask开发发拓展都暴露在flask.ext命名空间下，Flask-Bootstrap输出一个Bootstrap类
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap=Bootstrap(app)
app.config['UPLOADED_PHOTOS_DEST'] = 'D:/upload'  # 文件储存地址

photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # 文件大小限制，默认为16MB


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST' and 'photo' in request.files:
        print('upload picture')
        filename = photos.save(request.files['photo'])
        file_url = photos.url(filename)
        Transform.transform(app.config['UPLOADED_PHOTOS_DEST']+'/',filename)
        file_url2 = photos.url('temp.jpg')
        return render_template('test.html')+'<br><img src=' + file_url + '>'+ '<br><img src=' + file_url2 + '>'
    return render_template('index.html')
    
@app.route("/download",methods=['GET','POST'])
def download():
    if request.method =='POST':
        print('download txt')
        directory = app.config['UPLOADED_PHOTOS_DEST']
        filename='temp.txt'
        return send_from_directory(directory,filename,as_attachment=True)
        
if True:
    app.run()
