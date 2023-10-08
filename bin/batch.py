# Process an entire directory of images (presumably from the same day), and copy the
# GPS data from all files lacking it from the file nearest in time.

from datetime import datetime
from pathlib import Path
import sys
import pyexiv2

EXTS = [".jpg", ".arw"]
DTFMT = "%Y:%m:%d %H:%M:%S"
BASEDIR = "/home/mark/Pictures/2023/20230917.test"

# Pictures with a time delta greater than the following
# will not be modified
MAXDELTASECS = 400

imgfiles = sorted([p for p in Path(BASEDIR).glob("*") if p.suffix in EXTS])

goodfiles, badfiles = [], []
for imgfile in imgfiles:
    img = pyexiv2.Image(imgfile.as_posix())
    alldata = img.read_exif()
    tstamp = datetime.strptime(alldata["Exif.Image.DateTime"], DTFMT)

    data = {k: v for k, v in alldata.items() if "GPS" in k}
    data.update(filepath=imgfile)
    data.update(tstamp=tstamp)

    if "Exif.GPSInfo.GPSLongitude" in data:
        print(f"Found GPS data in {imgfile}")
        goodfiles.append(data)
    else:
        print(f"No GPS data in {imgfile}")
        badfiles.append(data)

if len(badfiles) == 0:
    print("Nothing to modify, exiting")
    sys.exit()

if len(goodfiles) == 0:
    print("No donor files found, exiting")
    sys.exit()

for bf in badfiles:
    print(f"{bf['filepath']}")
    bts = bf["tstamp"]
    mindsecs = 1e6
    minndx = -1
    for ndx, gf in enumerate(goodfiles):
        dsecs = abs((gf["tstamp"] - bts).total_seconds())
        if dsecs < mindsecs:
            mindsecs = dsecs
            minndx = ndx

    print(f"{minndx=}")

    if mindsecs < MAXDELTASECS:
        donordata = goodfiles[minndx]
        gpsdata = {k: v for k, v in donordata.items() if "GPS" in k}
        img = pyexiv2.Image(bf["filepath"].as_posix())
        img.modify_exif(gpsdata)
    else:
        print("Too far apart - not changing")
