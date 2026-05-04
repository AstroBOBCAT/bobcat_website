

def ra_hms2deg(ra_hms):
    hours, foo = ra_hms.split("h")
    mins, foo = foo.split("m")
    secs, foo = foo.split("s")

    ra_deg = (float(hours) + (float(mins) / 60) + (float(secs) / 3600)) * 15

    return ra_deg 
