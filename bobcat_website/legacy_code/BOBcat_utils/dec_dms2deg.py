import re

def dec_dms2deg(dec_dms):

    degrees, foo = dec_dms.split("d")
    mins, foo = foo.split("m")
    secs, foo = foo.split("s")
    #print(degrees, mins, secs)
    
    if (re.findall("^[-]", degrees)):
        minus = True
        degrees = degrees.replace("-", "")
       # print(degrees)

    dec_deg = (float(degrees) + (float(mins) / 60) + (float(secs) / 3600)) 
    
    if minus:
        dec_deg = -1 * dec_deg

    return dec_deg 