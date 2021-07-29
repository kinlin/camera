#!/usr/bin/env python3
import sys, math, os
import argparse
import numpy as np
#import cv2
from colour_demosaicing import demosaicing_CFA_Bayer_bilinear as demosaicing
from colour_hdri import (
        EXAMPLES_RESOURCES_DIRECTORY,
        tonemapping_operator_simple,
        tonemapping_operator_normalisation,
        tonemapping_operator_gamma,
        tonemapping_operator_logarithmic,
        tonemapping_operator_exponential,
        tonemapping_operator_logarithmic_mapping,
        tonemapping_operator_exponentiation_mapping,
        tonemapping_operator_Schlick1994,
        tonemapping_operator_Tumblin1999,
        tonemapping_operator_Reinhard2004,
        tonemapping_operator_filmic)
import matplotlib.pyplot as plt
import matplotlib.patches as patches
#from matplotlib.image import imsave
#from scipy.misc import imsave
from imageio import imwrite
from rawimage import *
#import rawpy
import  xml.dom.minidom
import datetime

#install
#py -m pip install colour_demosaicing
#py -m pip install imageio
#py -m pip install colour_hdri
#py -m pip install matplotlib
#py -m pip install numpy

g_ccm = np.array([[1.2085, -0.2502, 0.0417],
                  [-0.1174, 1.1625, -0.0452],
                  [0.0226, -0.2524, 1.2298]])

def rgb2gray(rgb):
    return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])

class DefaultParam():
    class Struct():
        def __init__(self, h, w, rawtype, bayer, stride):
            self.height   = h #1304
            self.width    = w #1152
            self.rawtype  = rawtype #'raw16'
            self.bayer    = bayer #'rggb'
            self.dgain    = 2.0
            self.stride   = stride
            print("DefaultParam stride: ", self.stride)
    def make_struct(self, h, w, rawtype, bayer, stride=None):
        if stride == None:
            return self.Struct(h, w, rawtype, bayer, 0)
        else:
            return self.Struct(h, w, rawtype, bayer, stride)

def process(args):
    #print(datetime.datetime.now(), args.rawtype, args.bayer, args.height, args.width, args.dgain, args.infile, args.outfile)
    print(datetime.datetime.now(), args.rawtype, args.bayer, args.height, args.width, args.dgain, args.infile, args.outfile, args.stride)

    rawmap = {'raw10': Raw10Image(args.infile, args.width, args.height, args.stride, args.offset, args.bayer),
              'raw'  : MipiRawImage(args.infile, args.width, args.height, args.stride, args.offset, args.bayer),
              'raw8': Raw8Image(args.infile, args.width, args.height, args.stride, args.offset, args.bayer),
              'raw16': Raw16Image(args.infile, args.width, args.height, args.stride, args.offset, args.bayer),
              'gray' : GrayImage(args.infile, args.width, args.height, args.offset),
              'yuv'  : YuvImage(args.infile, args.width, args.height, args.offset),
              'yvu'  : YvuImage(args.infile, args.width, args.height, args.offset)}

    if args.rawtype not in rawmap:
        print('unknown raw type:', args.rawtype)
        sys.exit(0)

    rawImage = rawmap[args.rawtype]
    rawImage.load()
    rgb = rawImage.getRGB()    
    return rgb

if "__main__" == __name__:
    defaultP = DefaultParam()
    #defaultP = defaultP.make_struct(2592, 1944, 'raw', 'rggb')       #raw10
    defaultP = defaultP.make_struct(3472, 4624, 'raw', 'rggb', 4672)       #raw10 need stride
    #defaultP = defaultP.make_struct(480, 640, 'yuv', 'rggb')       #raw10 need stride
    
    #defaultP = defaultP.make_struct(1304, 1152, 'raw16', 'rggb')       #raw16 ife port28 pd processed 
    #defaultP = defaultP.make_struct(1720, 1152, 'raw16', 'rggb')    #imx686   photo mode; mode1
    #defaultP = defaultP.make_struct(856, 576, 'raw16', 'rggb')    #imx686     mode11
    #defaultP = defaultP.make_struct(780, 1052, 'raw16', 'rggb')    #cam4 s5k3m5 mode0
    #defaultP = defaultP.make_struct(860, 4592, 'raw16', 'rggb')    #
    #defaultP = defaultP.make_struct(1304, 1152, 'raw16', 'rggb')    #video mode, imx686
    #defaultP = defaultP.make_struct(2592, 1944, 'raw', 'rggb')       #raw10


    
    parser = argparse.ArgumentParser(description='Show raw image or convert it to jpeg/png.',
                                    formatter_class=argparse.RawTextHelpFormatter)
    #parser.add_argument('-H', dest='height', type=int, required=True, default = defaultP.height)
    parser.add_argument('-H', dest='height', type=int, default = defaultP.height)
    parser.add_argument('-W', dest='width', type=int, default=defaultP.width)
    parser.add_argument('-s', dest='offset', type=int, default = 0)
    parser.add_argument('-t', dest='rawtype', choices = ['raw10', 'raw16', 'raw8', 'raw', 'gray', 'yuv', 'yvu'],
                        help='raw10 : continue 10bits\n'
                             'raw   : mipi 10bits\n'
                             'raw16 : 16bits\n'
                             'raw8  : 8bits\n'
                             'gray  : y 8bits\n'
                             'yuv   : yuv420 8bits\n'
                             'yvu   : yvu420 8bits',
                        default=defaultP.rawtype)
    parser.add_argument('-b', dest='bayer', choices=['rggb', 'bggr', 'grbg', 'gbrg'], default=defaultP.bayer)
    parser.add_argument('-d', dest='dgain', type=float, help='digit gain apply', default=defaultP.dgain)
    parser.add_argument('-S', dest='stride', type=int, help='stride of wide', default=defaultP.stride)
    parser.add_argument('-o', dest='outfile', metavar='FILE', help='write image to FILE')
    parser.add_argument('-i', dest='infile', metavar='InputRawFile', help='source raw image')
    parser.add_argument('-D', dest='inDir', metavar='InputDir', help='source raw image Dir')
    #parser.add_argument('infile', metavar='InputRawFile', help='source raw image')
    #parser.add_argument('inDir', metavar='InputDir', help='source dir')
    args = parser.parse_args()

    addRectangle = False

    if args.rawtype == None:
        args.rawtype = args.infile.split('.')[-1]

    print(args.inDir, args.infile)
    print("-----------------------------------")
    #sanity test
    if args.inDir==None and args.infile==None :
        print("No input, err")
        exit()
    print(args.inDir==None, args.infile==None)

    
    if args.inDir != None:
        #path="./camera"
        path=args.inDir
        dirs=os.listdir(path)
        for file in dirs:
            if file.split('.')[-1]=='raw':
                args.infile=path+'/'+file
                args.outfile=file.split('.')[0]+'.'+'jpg'
                rgb = process(args)
    
                rgb = tonemapping_operator_filmic(rgb)
    
                np.clip(rgb, 0.0, 1.0, out=rgb)
                #make it gray
                rgb=rgb2gray(rgb)
    
                #read xml
                #req00004_cam0_pdaf_input_lens_pos_Id_0320.raw -> ['req00004', 'cam0', 'pdaf', 'input', 'lens', 'pos', 'Id', '0320']
                #req00004_cam0_pdlib_buffer_meta_LensPos0320.xml -> ['req00004', 'cam0', 'pdlib', 'buffer', 'meta', 'LensPos0320']
                bufFile=file.split('.')[0].split('_')
                xmlFile=path+'/'+bufFile[0]+"_" + bufFile[1] + "_" + "pdlib_buffer_meta_LensPos" + bufFile[-1] + ".xml"
                if os.path.exists(xmlFile):
                    dom = xml.dom.minidom.parse(xmlFile)
                    root = dom.documentElement
                    startX=float(root.getElementsByTagName('startX')[0].childNodes[0].data)
                    startY=float(root.getElementsByTagName('startY')[0].childNodes[0].data)
                    endX=float(root.getElementsByTagName('endX')[0].childNodes[0].data)
                    endY=float(root.getElementsByTagName('endY')[0].childNodes[0].data)
                    addRectangle=True
                else:
                    startX, startY, endX, endY=0.3, 0.7, 0.3, 0.7
    
                #imwrite(args.outfile, rgb)  # this can also use to save the jpg
                #plt.figure(dpi=100)
    
                plt.figure(figsize=(defaultP.width/100, defaultP.height/100))
                plt.text(0,0,args.outfile)
                
                plt.imshow(rgb, cmap='Greys_r')
                currentAxis=plt.gca()
    
                if addRectangle==True:
                    f_width=defaultP.width
                    f_height=defaultP.height
                    left = startX*f_width
                    top = startY*f_height
                    width=(endX-startX)*f_width
                    height=(endY-startY)*f_height
                    #matplotlib.patches.Rectangle(xy, width, height, angle=0.0)     left, top, width, height
                    rect=patches.Rectangle((left, top), width, height,linewidth=2,edgecolor='r',facecolor='none')
                    currentAxis.add_patch(rect)
                plt.savefig(args.outfile)
                #imwrite(args.outfile, rgb)

    if args.infile != None:
        File=args.infile
        args.outfile=File.split('.')[0]+'.'+'jpg'
        print(args.outfile)
        rgb = process(args)
    
        if True:
            rgb = tonemapping_operator_filmic(rgb)
            np.clip(rgb, 0.0, 1.0, out=rgb)
            #make it gray; for rawtype == raw, 
            rgb=rgb2gray(rgb)
        
        if True:
            #plt.figure(figsize=(defaultP.width/100, defaultP.height/100))
            plt.imshow(rgb, cmap='Greys_r')
            #plt.imshow(rgb)
            #plt.show()
            plt.savefig(args.outfile)
        else:
            imwrite(args.outfile, rgb)  # this can also use to save the jpg
        
    #apply Gamma
    #seems have problem, not do it now

    #rgb = np.dot(rgb, g_ccm)

    #rgb = rgb / (rgb + 1)
    #rgb = tonemapping_operator_simple(rgb)

    #np.clip(rgb, 0.0, 1.0, out=rgb)
    #gray=rgb2gray(rgb)
    
    #if args.outfile:
    #    imwrite(args.outfile, rgb)
    #else:
    #   #plt.imshow(rgb)
    #    plt.imshow(gray, cmap='Greys_r')

    #    currentAxis=plt.gca()
    #    #matplotlib.patches.Rectangle(xy, width, height, angle=0.0)     left, top, width, height
    #    rect=patches.Rectangle((200, 600),550,650,linewidth=2,edgecolor='r',facecolor='none')
    #    currentAxis.add_patch(rect)

    #    plt.show()
        #plt.savefig('lena_new_sz.png')
