#!/user/bin/env python2
#
# Copyright (c) 2019-2019 kinlin <jlscut@gmail.com>
#

"""Implement of image process from pure raw10 to jpg"""

import os
import sys
import numpy
import copy
from PIL import Image
import random

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
