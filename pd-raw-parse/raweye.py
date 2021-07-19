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
    def __init__(self):
        self.height   = 1304 #1720
        self.width    = 1152
        self.rawtype  = 'raw16'
        self.bayer    = 'rggb'
        self.dgain    = 2.0

def process(args):
    print(datetime.datetime.now(), args.rawtype, args.bayer, args.height, args.width, args.dgain, args.infile, args.outfile)

    rawmap = {'raw10': Raw10Image(args.infile, args.width, args.height, args.offset, args.bayer),
              'raw'  : MipiRawImage(args.infile, args.width, args.height, args.offset, args.bayer),
              'raw8': Raw8Image(args.infile, args.width, args.height, args.offset, args.bayer),
              'raw16': Raw16Image(args.infile, args.width, args.height, args.offset, args.bayer),
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
    parser = argparse.ArgumentParser(description='Show raw image or convert it to jpeg/png.',
                                    formatter_class=argparse.RawTextHelpFormatter)
    #parser.add_argument('-H', dest='height', type=int, required=True, default = defaultP.height)
    parser.add_argument('-H', dest='height', type=int, default = defaultP.height)
    parser.add_argument('-W', dest='width', type=int)
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
    parser.add_argument('-o', dest='outfile', metavar='FILE', help='write image to FILE')
    parser.add_argument('infile', metavar='InputRawFile', help='source raw image')
    #parser.add_argument('inDir', metavar='InputDir', help='source dir')
    args = parser.parse_args()


    if args.rawtype == None:
        args.rawtype = args.infile.split('.')[-1]

    
    path="./camera"
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
            else:
                startX, startY, endX, endY=0.3, 0.7, 0.3, 0.7
            #imwrite(args.outfile, gray)
            plt.figure(dpi=100)
            plt.imshow(rgb, cmap='Greys_r')
            currentAxis=plt.gca()

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
