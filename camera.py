#!/user/bin/env python2
#
# Copyright (c) 2019-2019 kinlin <jlscut@gmail.com>
#

"""Implement of image process from pure raw10 to jpg"""

import os
import sys
import numpy
import math
import copy
from PIL import Image
import random

MAX_LUT_SIZE = 65536
DEFAULT_GAMMA_LUT = numpy.array(
        [math.floor(65535 * math.pow(i/65535.0, 1/2.2) + 0.5)
            for i in xrange(65536)])

def raw10_to_unpackRaw16(img, width, height):
    """Unpack a raw-10 capture to raw-16 capture.
    Args:
        img: the raw-10 img object
        resolution: contain width and height
    Returns:
        new Object of raw-16 data.

    """

    if width % 4 != 0:
        print "width not align to 4, Invalid raw-10 buffer width"

    #img = copy.deepcopy(img)
    #print img.reshape(4,5)
    #img=img.reshape(1944, 3248)
    print "after reshape: "+ str(len(img))
    newimg = unpack_raw10_image(img, width, height)
    return newimg

def unpack_raw10_image(img, w, h):
    """Unpack a raw-10 img

    Args:
        img: A raw-10 image, as a uint8 numpy array

    Returns:
        Image as a uint16 numpy array, with all row padding stripped.
    """
   # if img.shape[1] % 5 != 0:
   #     print "Invalid raw-10 buffer width"

    stride=3248
    print len(img)
    #cut out the 4x8b MSBs and shift to bits [9:2] in 16b words.
    img=img.reshape(1944, 3248)
    img=numpy.delete(img, -1, 1)
    img=numpy.delete(img, -1, 1)
    img=numpy.delete(img, -1, 1)
    img=numpy.delete(img, -1, 1)
    img=numpy.delete(img, -1, 1)
    img=numpy.delete(img, -1, 1)
    img=numpy.delete(img, -1, 1)
    img=numpy.delete(img, -1, 1)
    print "after delete last stride: "+str(len(img))
    msbs = numpy.delete(img, numpy.s_[4::5], 1)
    print "numpy.delete:"
    print len(msbs)
    msbs = msbs.astype(numpy.uint16)
    print "astype uint16"
    print len(msbs)
    msbs = numpy.left_shift(msbs, 2) #example: np.right_shift(10,1) ->5(101)
    print "left_shift:"
    print len(msbs)
    
    msbs = msbs.reshape(h, w)

    #Cut out the 4x2b LSBs and put each in bits [1:0] of their own 8b words
    lsbs = img[::, 4::5].reshape(h,w/4)
    lsbs = numpy.right_shift(
            numpy.packbits(numpy.unpackbits(lsbs).reshape(h,w/4,4,2),3), 6)
    # Pair the LSB bits group to pixel 0 instead of pixel 3
    lsbs = lsbs.reshape(h,w/4,4)[:,:,::-1]
    lsbs = lsbs.reshape(h,w)
    # Fuse the MSBs and LSBs back together
    img16 = numpy.bitwise_or(msbs, lsbs).reshape(h,w)
    return img16


def seperateRGB(img, w, h):
    """Separate the image planes.
    Returns:
        Nomalize the plain to R Gr Gb B

    """
    imgs = [img[::2].reshape(w*h/2)[::2].reshape(h/2,w/2,1),
            img[::2].reshape(w*h/2)[1::2].reshape(h/2,w/2,1),
            img[1::2].reshape(w*h/2)[::2].reshape(h/2,w/2,1),
            img[1::2].reshape(w*h/2)[1::2].reshape(h/2,w/2,1)]
    
    cfa_pattern = get_cfa_order(1)
    return [imgs[i] for i in cfa_pattern]
    #for testing , I just assume it's 

def get_cfa_order(config):
    """
    Return a mapping from the Bayer 2x2 top-left grid in the CFA to the standard order R, Gr, Gb, B.

    Args:
        config: 
          1.RG   2.GR   3.GB    4.BG
            GB     BG     RG      GR
    Returns:
        use 4 int, correspoding positions
    """
    if config == 1:
        #RGGB
        return [0,1,2,3]
    elif config == 2:
        #GRBG
        return [1,0,3,2]
    elif config == 3:
        #GBRG
        return [2,3,0,1]
    elif config == 4:
        return [3,2,1,0]
    else:
        print "Not Supported CFA"


def convert_rawRGGB_to_rgbImage(r_plane, gr_plane, gb_plane, b_plane):
    """Convert Bayer raw-16 image to RGB image.

    What process can we add here?

    gains?

    CCM?

    """

    #now we get R=R, G=(Gr+Gb)/2, B=B
    img = numpy.dstack([r_plane, (gr_plane+gb_plane)/2.0, b_plane])

    #TODO: Process needed

    return img



def write_image(img, fname, apply_gamma=False):
    """Save a float-3 numpy array image to a file, Use PIL

    now the Image is 3-channel as RGB, or 1-channel as greyscale
    

    """

    if apply_gamma:
        img = apply_lut_to_image(img, DEFAULT_GAMMA_LUT)

    (h, w, chans) = img.shape
    if chans == 3:
        #img=Image.fromarray((img*255.0).astype(numpy.uint8), "RGB")
        img=Image.fromarray((img).astype(numpy.uint8), "RGB")
        img.save(fname)
    elif chans == 1:
       # img3 = (img*255.0).astype(numpy.uint8).repeat(3).reshape(h,w,3)
        img3 = (img).astype(numpy.uint8).repeat(3).reshape(h,w,3)
    else:
        print "Unsupported image type"


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
    print "lut n: %d" %n
    if n<=0 or n> MAX_LUT_SIZE or (n & (n - 1)) != 0:
        print "Invalid arg LUT size: %d" %n
    m = float(n-1)
    return (lut[(img*m).astype(numpy.uint16)] / m).astype(numpy.float32)


if __name__ == "__main__":
    #test img: 2592_1944_stride3248.raw
    fp = open('2592_1944_stride3248.raw')
    img=fp.read()
    #fp.close()

    #convert from string to array
    img_array = numpy.fromstring(img, numpy.uint8)
    #img_array = numpy.array([i+random.randint(0, 200) for i in range(1, 21)])
    #print img_array
    print "img_array"
    print len(img_array)
    new = raw10_to_unpackRaw16(img_array, 2592, 1944)
    fp = open('test.raw', 'wb')
    fp.write(new)
    fp.close()

    r, gr, gb, b = seperateRGB(new, 2592, 1944)
    img = convert_rawRGGB_to_rgbImage(r, gr, gb, b)
    img = write_image(img, "2592_1944_stride3248.jpg", True)
