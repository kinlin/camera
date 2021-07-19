#!/usr/bin/env python3
import sys, math, os
import argparse
import numpy as np
import cv2
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

g_ccm = np.array([[1.2085, -0.2502, 0.0417],
                  [-0.1174, 1.1625, -0.0452],
                  [0.0226, -0.2524, 1.2298]])
MAX_LUT_SIZE = 65536
DEFAULT_GAMMA_LUT = np.array(
        [math.floor(65535 * math.pow(i/65535.0, 1/2.2) + 0.5)
            for i in range(65536)])

            
def apply_lut_to_image(img, lut):
    """Applies a LUT to every pixel in a float image array.
     Internally converts to a 16b integer image, since the LUT can work with up
     to 16b->16b mappings (i.e. values in the range [0,65535]). The lut can also
     have fewer than 65536 entries, however it must be sized as a power of     2
     (and for smaller luts, the scale must match the bitdepth).

     For a 16b lut of 65536 entries, the operation performed is:

         lut[r * 65535] / 65535 -> r'
         lut[g * 65535] / 65535 -> g'
         lut[b * 65535] / 65535 -> b'
     For a 10b lut of 1024 entries, the operation becomes:
         lut[r * 1023] / 1023 -> r'
         lut[g * 1023] / 1023 -> g'
         lut[b * 1023] / 1023 -> b'

     Args:
         img: Numpy float image array, with pixel values in [0,1].
         lut: Numpy table encoding a LUT, mapping 16b integer values.

     Returns:
         Float image array after applying LUT to each pixel.

    """
    n = len(lut)

    if n<=0 or n> MAX_LUT_SIZE or (n & (n - 1)) != 0:
        logger.error("Invalid arg LUT size: %d", n)
    m = float(n-1)
    return (lut[(img*m).astype(np.uint16)] / m).astype(np.float32)


def rgb2gray(rgb):
    return np.dot(rgb[...,:3], [0.299, 0.587, 0.114])

class DefaultParam():
    def __init__(self):
        self.height   = 1720
        self.width    = 1152
        self.rawtype  = 'raw16'
        self.bayer    = 'rggb'
        self.dgain    = 2.0



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
        print(file)
        print
    
    
    print(args.rawtype, args.bayer, args.height, args.width, args.dgain, args.infile, args.outfile)

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

    #apply Gamma
    #seems have problem, not do it now
    #rgb = apply_lut_to_image(rgb, DEFAULT_GAMMA_LUT)

    #rgb = np.dot(rgb, g_ccm)


    #rgb = rgb / (rgb + 1)
    #rgb = tonemapping_operator_simple(rgb)

    np.clip(rgb, 0.0, 1.0, out=rgb)

    gray=rgb2gray(rgb)

    
    if args.outfile:
        imwrite(args.outfile, rgb)
    else:
        #plt.imshow(rgb)
        plt.imshow(gray, cmap='Greys_r')

        currentAxis=plt.gca()
        #matplotlib.patches.Rectangle(xy, width, height, angle=0.0)     left, top, width, height
        rect=patches.Rectangle((200, 600),550,650,linewidth=2,edgecolor='r',facecolor='none')
        currentAxis.add_patch(rect)
        
        
        plt.show()
        #plt.savefig('lena_new_sz.png')
