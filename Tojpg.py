# -*- coding: utf-8 -*-

import os
from PIL import Image, ImageFont, ImageDraw

def getHeight(filename):
    height=0
    f=open(filename)
    for line in f.readlines():
        height=height+1
    return height
def getWidth(filename):
    width=0
    f=open(filename)
    return len(f.readline())
def toJpg(directory,filename):
    height=6.33*getHeight(directory+filename)*3
    #height=5.9090909*getHeight(filename)*3
    width=5.657*getWidth(directory+filename)*3
    im = Image.new("RGB", (int(width), int(height)), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    font = ImageFont.truetype(os.path.join("fonts", "consola.ttf"), 30)
    x=1
    y=1
    f=open(directory+filename)
    for str in f.readlines():
        if y%38==1:
            dr.text((x, y), str.strip(), font=font, fill="#000000")
        y=y+19
    f.close()
    im=im.resize((int(im.size[0]*0.3), int(im.size[1]*0.3)))#调整图片大小
    #im.show()
    savedname='temp.jpg'
    im.save(directory+savedname)