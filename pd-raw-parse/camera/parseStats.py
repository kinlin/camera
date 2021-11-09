import matplotlib
import sys
from PIL import Image
import numpy
import math
import struct
import ctypes as ct

totalSize=64*48;
#IFEOutputPortStatsAWBBG          = 21;
#AWBBG stats struct, different HW has different stats
#/// @brief Memory map of raw hardware AWB BG v1.7 stats region
#struct BG17StatsRegionOutput
#{
#    UINT64  sum         : 34;       ///< Region Sum
#    UINT32  reserved1   : 14;       ///< reserved
#    UINT32  count       : 16;       ///< Region count
#} CAMX_PACKED;
#
#/// @brief Memory map of raw hardware AWB BG v1.7 stats region
#struct AWBBGStats17HwOutput
#{
#    BG17StatsRegionOutput    unsaturatedR;  ///< Unsaturated R Region
#    BG17StatsRegionOutput    unsaturatedGr; ///< Unsaturated Gr Region
#    BG17StatsRegionOutput    unsaturatedGb; ///< Unsaturated Gb Region
#    BG17StatsRegionOutput    unsaturatedB;  ///< Unsaturated B Region
#    BG17StatsRegionOutput    unsaturatedY;  ///< Unsaturated Y Region
#
#    BG17StatsRegionOutput    saturatedR;    ///< Saturated R Region
#    BG17StatsRegionOutput    saturatedGr;   ///< Saturated Gr Region
#    BG17StatsRegionOutput    saturatedGb;   ///< Saturated Gb Region
#    BG17StatsRegionOutput    saturatedB;    ///< Saturated B Region
#    BG17StatsRegionOutput    saturatedY;    ///< Saturated Y Region
#} CAMX_PACKED;

#Format String首位代表字符大小端
#--> @   native
#--> =   native
#--> <   little-endian
#--> >   big-endian
#--> !   network(=big-endian)

IHist12={}
class IHist12(ct.Structure):
    _fields_ = [
                ("YCCHistorgram",  ct.c_uint16),
                ("greenHistogram", ct.c_uint16),
                ("blueHistogram",  ct.c_uint16),
                ("redHistogram",   ct.c_uint16)]
               # ("padding1",       ct.c_uint16),
               # ("padding2",       ct.c_uint16),
               # ("padding3",       ct.c_uint16),
               # ("padding4",       ct.c_uint16)]
                
def parseIHist12():
    results = []
    struct_fmt=">HHHHHHHH"
    struct_len=struct.calcsize(struct_fmt)
    print(struct_len)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    with open('IHIST_IFE[0]_[out]_port[15]_w[4096]_h[1].BLOB', 'rb') as f:
        for index in range(256):
            data = f.read(struct_len)
            if data:
                s = struct_unpack(data)
                #print(index)
                stats = IHist12()
                stats.YCCHistorgram   = s[0]
                stats.greenHistogram  = s[1]
                stats.blueHistogram   = s[2]
                stats.redHistogram    = s[3]
                stats.padding1        = s[4]
                stats.padding2        = s[5]
                stats.padding3        = s[6]
                stats.padding4        = s[7]
                results.append(stats)
                print("---index:%d---", index)
                print(results[index].YCCHistorgram, results[index].greenHistogram, results[index].blueHistogram, results[index].redHistogram,
                      results[index].padding1, results[index].padding2, results[index].padding3, results[index].padding4)



BGStats={}
class BGStats(ct.Structure):
    _fields_ = [
                ("unsaturatedR",   ct.c_uint64),
                ("unsaturatedGr",  ct.c_uint64),
                ("unsaturatedGb",  ct.c_uint64),
                ("unsaturatedB",   ct.c_uint64),
                ("unsaturatedY",   ct.c_uint64),
                ("saturatedR",     ct.c_uint64),
                ("saturatedGr",    ct.c_uint64),
                ("saturatedGb",    ct.c_uint64),
                ("saturatedB",     ct.c_uint64),
                ("saturatedY",     ct.c_uint64) ]
                

#A:ParseAWBBGOutput() unsatu-(sum,count):R(74519710, 1296) B(62067816, 1296), Gr(131102660, 1296), Gb(130010144, 1296), Y(0, 1296)
#A:ParseAWBBGOutput() satu-(sum,count):R(0, 0) B(0, 0), Gr(0, 0), Gb(0, 0), Y(0, 0)
#-----
#B:ParseAWBBGOutput() unsatu-(sum,count):R(0, 0) B(0, 0), Gr(0, 0), Gb(0, 0), Y(0, 0)
#B:ParseAWBBGOutput() satu-(sum,count):R(192184857, 1296) B(213349484, 1296), Gr(339359239, 1296), Gb(339331964, 1296), Y(0, 1296)
#back camera: count is 1296   Front camera: count is 1936
#ParseAWBBGConfig() QDEBUG h:64, v:48, total:3072, depth:18

#数据二进制
# 0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
#b9 0e 2f 01 20 20 10 05 55 d9 47 02 20 20 10 05
#a7 0d 42 02 20 20 10 05 f4 30 31 01 20 20 10 05  
# file size: 1384448   max size: 160*90*4*12*2=1382400
def parseBG17Stats():
    BG_width  = 64
    BG_height = 48
    results   = []
    # = : default;     <: little-enddien         >:big-enddien
    struct_fmt='<QQQQQQQQQQ'
    struct_len=struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from

    with open('IFE[0]_[out]_port[21]_w[1382400]_h[1]_stride[1382400]_scanline[1]-frontcam-waipio.BLOB', 'rb') as f:
        for index in range(BG_width*BG_height):
            data = f.read(struct_len)
            if data:
                s = struct_unpack(data)
                #print("%x"%s[0])   #5100000012f0eb9    print little-enddien
                #print("---index:%d---"%index);
                print(s[0]>>48,s[0]&0x3FFFFFFFF, 
                      s[1]>>48,s[1]&0x3FFFFFFFF,
                      s[2]>>48,s[2]&0x3FFFFFFFF,
                      s[3]>>48,s[3]&0x3FFFFFFFF,
                      s[4]>>48,s[4]&0x3FFFFFFFF,
                      s[5]>>48,s[5]&0x3FFFFFFFF,
                      s[6]>>48,s[6]&0x3FFFFFFFF,
                      s[7]>>48,s[7]&0x3FFFFFFFF,
                      s[8]>>48,s[8]&0x3FFFFFFFF,
                      s[9]>>48,s[9]&0x3FFFFFFFF)

#waipio 680
#0x3FFFFFFFF <=> 17179869183
#ParseTintlessBGStatsConfig() QDEBUG h:32, v:24, total:768, depth:18
#front cam:ParseTintlessBGOutput() unsatu-(sum,count):R(259750240, 7744) B(177406528, 7744), Gr(337874480, 7744), Gb(346923312, 7744), Y(0, 7744)
#back  cam:ParseTintlessBGOutput() unsatu-(sum,count):R(136927616, 5184) B(118760048, 5184), Gr(238585680, 5184), Gb(236942544, 5184), Y(0, 5184)
def parseTLBG17Stats():
    BG_width  = 32
    BG_height = 24
    results   = []
    # = : default;     <: little-enddien         >:big-enddien
    struct_fmt='<QQQQQQQQQQ'
    struct_len=struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    with open('TLBG_IFE[0]_[out]_port[19]_w[294912]_h[1].BLOB', 'rb') as f:
        for index in range(BG_width*BG_height):
            data = f.read(struct_len)
            if data:
                s = struct_unpack(data)
                #print("%x"%s[0])   #5100000012f0eb9    print little-enddien
                #print("---index:%d---"%index);
                print(s[0]>>48,s[0]&0x3FFFFFFFF, 
                      s[1]>>48,s[1]&0x3FFFFFFFF,
                      s[2]>>48,s[2]&0x3FFFFFFFF,
                      s[3]>>48,s[3]&0x3FFFFFFFF,
                      s[4]>>48,s[4]&0x3FFFFFFFF,
                      s[5]>>48,s[5]&0x3FFFFFFFF,
                      s[6]>>48,s[6]&0x3FFFFFFFF,
                      s[7]>>48,s[7]&0x3FFFFFFFF,
                      s[8]>>48,s[8]&0x3FFFFFFFF,
                      s[9]>>48,s[9]&0x3FFFFFFFF)
#waipio： IFEOutputPortStatsAECBE          = 30;
#---------------Back:
#ParseAECBEConfig() QDEBUG h:32, v:32, total:1024, depth:18
#ParseAECBEStatsBuffer() AECBEStats unsat R(210910733, 3888), B(169086460, 3888), GR(358203885, 3888), GB(359494122, 3888), Y(288897414, 3888)
#ParseAECBEStatsBuffer() AECBEStats sat R(0, 0), B(0, 0), GR(0, 0), GB(0, 0), Y(0, 0)
#---------------Front:
#ParseAECBEConfig() QDEBUG h:32, v:32, total:1024, depth:18
#ParseAECBEStatsBuffer() AECBEStats unsat R(248589448, 5808), B(161605664, 5808), GR(332679939, 5808), GB(341224636, 5808), Y(287419796, 5808)
#ParseAECBEStatsBuffer() AECBEStats sat R(0, 0), B(0, 0), GR(0, 0), GB(0, 0), Y(0, 0)
def parseAECBE17Stats():
    BG_width  = 32
    BG_height = 24
    results   = []
    # = : default;     <: little-enddien         >:big-enddien
    struct_fmt='<QQQQQQQQQQ'
    struct_len=struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    with open('IFE[0]_[out]_port[30]_w[655360]_h[1]_stride[655360]_scanline[1].BLOB', 'rb') as f:
        for index in range(BG_width*BG_height):
            data = f.read(struct_len)
            if data:
                s = struct_unpack(data)
                #print("%x"%s[0])   #5100000012f0eb9    print little-enddien
                #print("---index:%d---"%index);
                print(s[0]>>48,s[0]&0x3FFFFFFFF, 
                      s[1]>>48,s[1]&0x3FFFFFFFF,
                      s[2]>>48,s[2]&0x3FFFFFFFF,
                      s[3]>>48,s[3]&0x3FFFFFFFF,
                      s[4]>>48,s[4]&0x3FFFFFFFF,
                      s[5]>>48,s[5]&0x3FFFFFFFF,
                      s[6]>>48,s[6]&0x3FFFFFFFF,
                      s[7]>>48,s[7]&0x3FFFFFFFF,
                      s[8]>>48,s[8]&0x3FFFFFFFF,
                      s[9]>>48,s[9]&0x3FFFFFFFF)


#Waipio
#IFEOutputPortStatsAECBHIST       = 36;
#ParseAECBHistStats() QDEBUG-AECBHist, total:1024
# 444 /// @brief Memory map of raw hardware BHist v1.4 stats
# 445 struct BHistStatsHwOutput                                                                                                                                                                    446 {
# 447     UINT32  histogramBin    : 25;
# 448     UINT32  reserved        : 7;
# 449 }CAMX_PACKED;
class AECBHist14(ct.Structure):
    _fields_ = [("histogramBin",  ct.c_uint32)]

def parseAECBHist():
    numOfBin  = 1024;
    results   = []

    # = : default;     <: little-enddien     >:big-enddien
    struct_fmt='<L'
    struct_len=struct.calcsize(struct_fmt)
    struct_unpack = struct.Struct(struct_fmt).unpack_from
    with open('IFE[0]_[out]_port[36]_w[32768]_h[1]_stride[32768]_scanline[1].BLOB', 'rb') as f:
        for index in range(numOfBin):
            data = f.read(struct_len)
            AECBHist  = AECBHist14()
            if data:
                s = struct_unpack(data)
                #print("index:%d, %x ->%d -->%d"%(index, s[0], s[0], s[0]&0x1FFFFFF))   #    print little-enddien
                AECBHist.histogramBin = s[0]
                results.append(AECBHist)
                #print("index:%d, %x  -->%d"%(index, results[index].histogramBin, results[index].histogramBin&0x1FFFFFF))   #    print little-enddien

    #for i in range(1024):
    #    print("i:%d, hist:%d"%(i, results[i].histogramBin))

def main():
    #parseAECBHist()
    #parseAECBE17Stats()
    #parseTLBG17Stats()
    #parseBG17Stats()
    #parseIHist12()


if __name__ == "__main__":
    main()
