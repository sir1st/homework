#coding:utf-8
from flask import Flask,render_template,send_from_directory,request
#from flask.ext.bootstrap import Bootstrap #专为Flask开发发拓展都暴露在flask.ext命名空间下，Flask-Bootstrap输出一个Bootstrap类
from flask_bootstrap import Bootstrap
app=Flask(__name__)
bootstrap=Bootstrap(app)#Flask扩展一般都在创建实例时初始化，这行代码是Flask-Bootstrap的初始化方法
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')
@app.route('/Download',methods=['GET','POST'])
def Download():
    if request.method=='POST':
        return send_from_directory('D:/upload','temp.txt',as_attachment=True)
if True:
    app.run()