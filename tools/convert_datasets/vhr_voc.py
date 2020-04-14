from lxml.etree import Element,SubElement,tostring
from xml.dom.minidom import parseString
import xml.dom.minidom
import os
import sys
from PIL import Image
import pdb as ipdb

#把txt中的内容写进xml
def deal(path):
    files=os.listdir(path)#列出所有文件
    for file in files:
        filename=os.path.splitext(file)[0]#分割出文件名
        #print(filename)
        sufix=os.path.splitext(file)[1]#分割出后缀
        # ipdb.set_trace()
        if sufix=='.txt':
            xmins=[]
            ymins=[]
            xmaxs=[]
            ymaxs=[]
            names=[]
            num,xmins,ymins,xmaxs,ymaxs,names=readtxt(file)
            dealpath=path+"/"+filename+".xml"
            filename=filename+'.jpg'
            with open(dealpath,'w') as f:
                writexml(dealpath,filename,num,xmins,ymins,xmaxs,ymaxs,names)

#读取图片的高和宽写入xml        
def dealwh(path):
    files=os.listdir(path)#列出所有文件
    for file in files:
        filename=os.path.splitext(file)[0]#分割出文件名
        sufix=os.path.splitext(file)[1]#分割出后缀
        if sufix=='.jpg':
            height,width=readsize(file)
            dealpath=path+"/"+filename+".xml"
            gxml(dealpath,height,width)

#读取txt文件
def readtxt(path):
    with open(path,'r') as f:
        contents=f.read()
        #print(contents)
        objects=contents.split('\n')#分割出每个物体
        for i in range(objects.count('')):#去掉空格项
           objects.remove('')
        #print(objects)
        num=len(objects)#物体的数量
        #print(num)
        xmins=[]
        ymins=[]
        xmaxs=[]
        ymaxs=[]
        names=[]
        for objecto in objects:
            #print(objecto)	
            xmin=objecto.split(',')[0]
            xmin=xmin.split('(')[1]
            xmin=xmin.strip()
            # ipdb.set_trace()
			
            ymin=objecto.split(',')[1]
            ymin=ymin.split(')')[0]
            ymin=ymin.strip()
			
            xmax=objecto.split(',')[2]
            xmax=xmax.split('(')[1]
            xmax=xmax.strip()
			
            ymax=objecto.split(',')[3]
            ymax=ymax.split(')')[0]
            ymax=ymax.strip()
			
            name=objecto.split(',')[4]
            name=name.strip()
			
            if name=="1 " or name=="1":
                name='airplane'
            elif name=="2 "or name=="2":
                name='ship'
            elif name== "3 "or name=="3":
                name='storage tank'
            elif name=="4 "or name=="4":
                name='baseball diamond'
            elif name=="5 "or name=="5":
                name='tennis court'
            elif name=="6 "or name=="6":
                name='basketball court'
            elif name=="7 "or name=="7":
                name='ground track field'
            elif name=="8 "or name=="8":
                name='habor'
            elif name=="9 "or name=="9":
                name='bridge'
            elif name=="10 "or name=="10":
                name='vehicle'	
            else:
                print(path)			
            #print(xmin,ymin,xmax,ymax,name)
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)
            names.append(name)
        #print(num,xmins,ymins,xmaxs,ymaxs,names)
        return num,xmins,ymins,xmaxs,ymaxs,names

#在xml文件中添加宽和高
def gxml(path,height,width):
    dom=xml.dom.minidom.parse(path)
    root=dom.documentElement
    heights=root.getElementsByTagName('height')[0]
    heights.firstChild.data=height
    #print(height)

    widths=root.getElementsByTagName('width')[0]
    widths.firstChild.data=width
    #print(width)
    with open(path, 'w') as f:
        dom.writexml(f)
    return

#创建xml文件
def writexml(path,filename,num,xmins,ymins,xmaxs,ymaxs,names,height='256',width='256'):    
    node_root=Element('annotation')

    node_folder=SubElement(node_root,'folder')
    node_folder.text="VOC2007"

    node_filename=SubElement(node_root,'filename')
    node_filename.text="%s" % filename

    node_size=SubElement(node_root,"size")
    node_width = SubElement(node_size, 'width')
    node_width.text = '%s' % width

    node_height = SubElement(node_size, 'height')
    node_height.text = '%s' % height

    node_depth = SubElement(node_size, 'depth')
    node_depth.text = '3'
    for i in range(num):
        node_object = SubElement(node_root, 'object')
        node_name = SubElement(node_object, 'name')
        node_name.text = '%s' % names[i]
        node_name = SubElement(node_object, 'pose')
        node_name.text = '%s' % "unspecified"
        node_name = SubElement(node_object, 'truncated')
        node_name.text = '%s' % "0"
        node_difficult = SubElement(node_object, 'difficult')
        node_difficult.text = '0'
        node_bndbox = SubElement(node_object, 'bndbox')
        node_xmin = SubElement(node_bndbox, 'xmin')
        node_xmin.text = '%s'% xmins[i]
        node_ymin = SubElement(node_bndbox, 'ymin')
        node_ymin.text = '%s' % ymins[i]
        node_xmax = SubElement(node_bndbox, 'xmax')
        node_xmax.text = '%s' % xmaxs[i]
        node_ymax = SubElement(node_bndbox, 'ymax')
        node_ymax.text = '%s' % ymaxs[i]

    xml = tostring(node_root, pretty_print=True)  
    dom = parseString(xml)
    with open(path, 'wb') as f:
        f.write(xml)
    return

def readsize(path):
    img=Image.open(path)
    width=img.size[0]
    height=img.size[1]
    return height,width

if __name__ == "__main__":
    path=("./")
    deal(path)
    dealwh(path)