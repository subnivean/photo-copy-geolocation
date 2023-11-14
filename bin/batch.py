# Process an entire directory of images (presumably from the same day), and copy the
# GPS data from all files lacking it from the file nearest in time.

from datetime import datetime, timedelta
from pathlib import Path
import sys
import pyexiv2

EXTS = [".jpg", ".arw"]
DTFMT = "%Y:%m:%d %H:%M:%S"
GPSDSKEY = "Exif.GPSInfo.GPSDateStamp"
GPSTSKEY = "Exif.GPSInfo.GPSTimeStamp"
GPSLONGKEY = "Exif.GPSInfo.GPSLongitude"
TZOFFSETKEY = "Exif.Photo.OffsetTime"
IMGDATETIMEKEY = "Exif.Image.DateTime"

# Pictures with a time delta greater than the following
# will not be modified
MAXDELTASECS = 600


def make_gps_datetimestamp(alldata):
    """Make the GPS Date/Time stamp from the exif data"""
    gyr, gmon, gday = [int(f) for f in alldata[GPSDSKEY].split(":")]
    ghr, gmin, gsec = [int(eval(s)) for s in alldata[GPSTSKEY].split()]
    gdts = datetime(gyr, gmon, gday, ghr, gmin, gsec)
    tzoffset = int(alldata[TZOFFSETKEY].split(":")[0])
    return gdts + timedelta(hours=tzoffset)


myargv = sys.argv

dryrun = False
if "-t" in myargv:
    dryrun = True
    myargv.remove("-t")

if not dryrun:
    print("This is for real - Ctrl-C now, or let 'er rip!")
    input()

folder = myargv[1]
basedir = f"/home/mark/Pictures/{folder[0:4]}/{folder}"

imgfiles = sorted([p for p in Path(basedir).glob("*") if p.suffix in EXTS])

gooddata, baddata = [], []
for imgfile in imgfiles:
    img = pyexiv2.Image(imgfile.as_posix())
    alldata = img.read_exif()

    data = {k: v for k, v in alldata.items() if "GPS" in k}

    dtstamp = datetime.strptime(alldata[IMGDATETIMEKEY], DTFMT)
    data.update(filepath=imgfile, dtstamp=dtstamp)

    if GPSLONGKEY in data:
        print(f"Found GPS data in {imgfile}")
        data["dtstamp"] = make_gps_datetimestamp(alldata)
        gooddata.append(data)
    else:
        print(f"   No GPS data in {imgfile}")
        baddata.append(data)

if len(baddata) == 0:
    print("Nothing to modify, exiting")
    sys.exit()

if len(gooddata) == 0:
    print("No donor files found, exiting")
    sys.exit()

for bf in baddata:
    print()
    print(f"Bad:  {bf['filepath']}")
    bts = bf["dtstamp"]
    mindsecs = 1e6
    minndx = -1
    for ndx, gf in enumerate(gooddata):
        dsecs = abs((gf["dtstamp"] - bts).total_seconds())
        if dsecs < mindsecs:
            mindsecs = dsecs
            minndx = ndx

    # print(f"{minndx=}")

    if mindsecs < MAXDELTASECS:
        donordata = gooddata[minndx]
        print(
            f"Using {donordata['filepath']} as donor\n     ({donordata['dtstamp'].isoformat()=})"
        )
        gpsdata = {k: v for k, v in donordata.items() if "GPS" in k}
        img = pyexiv2.Image(bf["filepath"].as_posix())
        if dryrun is False:
            img.modify_exif(gpsdata)
            img.close()
        else:
            print("Dry run is on - not changing file")
    else:
        print(" *** Too far apart - not changing ***")
