#!/usr/bin/env python

"""
Pegasus DAX generator for the Montage toolkit. The generated
workflow will support multiple bands and colors to produce
a color image.

#  Copyright 2016 University Of Southern California
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""

import os
import argparse
import re
import subprocess
import sys

#Insert this directory in our search path
os.sys.path.insert(0, os.getcwd())

from AutoADAG import *
from Pegasus.DAX3 import *
from astropy.io import ascii

common_files = {}
replica_catalog = {}


def which(file):
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(os.path.join(path, file)):
            return os.path.join(path, file)
    return None


def add_transformations(dax):
    """
    Some transformations in Montage uses multiple executables
    """
    exes = {}
    base_dir = os.path.dirname(which("mProject"))
    for fname in os.listdir(base_dir):
        if fname[0] == ".":
            continue
        e = Executable(fname, arch = "x86_64", installed = False)
        e.addPFN(PFN("file://" + base_dir + "/" + fname, "local"))
        exes[fname] = e
    # only add the ones we actually need
    for tname in ["mProject", "mDiff", "mFitplane", "mDiffFit", \
                  "mConcatFit", "mBgModel", "mBackground", "mImgtbl", \
                  "mAdd", "mJPEG"]:
        t = Transformation(tname)
        if tname == "mDiffFit":
            t.uses(exes["mDiff"])
            t.uses(exes["mFitplane"])
        t.uses(exes[tname])
        dax.addExecutable(exes[tname])
        dax.addTransformation(t)


def generate_region_hdr(dax, center, degrees):

    global common_files

    (crval1, crval2) = center.split()
    crval1 = float(crval1)
    crval2 = float(crval2)

    cdelt = 0.000278
    naxis = int((float(degrees) / cdelt) + 0.5)
    crpix = (naxis + 1) / 2.0

    f = open("data/region.hdr", "w")
    f.write("SIMPLE  = T\n")
    f.write("BITPIX  = -64\n")
    f.write("NAXIS   = 2\n")
    f.write("NAXIS1  = %d\n" %(naxis))
    f.write("NAXIS2  = %d\n" %(naxis))
    f.write("CTYPE1  = 'RA---TAN'\n")
    f.write("CTYPE2  = 'DEC--TAN'\n")
    f.write("CRVAL1  = %.6f\n" %(crval1))
    f.write("CRVAL2  = %.6f\n" %(crval2))
    f.write("CRPIX1  = %.6f\n" %(crpix))
    f.write("CRPIX2  = %.6f\n" %(crpix))
    f.write("CDELT1  = %.9f\n" %(-cdelt))
    f.write("CDELT2  = %.9f\n" %(cdelt))
    f.write("CROTA2  = %.6f\n" %(0.0))
    f.write("EQUINOX = %d\n" %(2000))
    f.close()

    common_files["region.hdr"] = File("region.hdr")
    replica_catalog["region.hdr"] = {"url": "file://" + os.getcwd() + "/data/region.hdr", "site_label": "local"}

    # we also need an oversized region which will be used in the first part of the 
    # workflow to get the background correction correct
    f = open("data/region-oversized.hdr", "w")
    f.write("SIMPLE  = T\n")
    f.write("BITPIX  = -64\n")
    f.write("NAXIS   = 2\n")
    f.write("NAXIS1  = %d\n" %(naxis + 5000))
    f.write("NAXIS2  = %d\n" %(naxis + 5000))
    f.write("CTYPE1  = 'RA---TAN'\n")
    f.write("CTYPE2  = 'DEC--TAN'\n")
    f.write("CRVAL1  = %.6f\n" %(crval1))
    f.write("CRVAL2  = %.6f\n" %(crval2))
    f.write("CRPIX1  = %.6f\n" %(crpix + 2500))
    f.write("CRPIX2  = %.6f\n" %(crpix + 2500))
    f.write("CDELT1  = %.9f\n" %(-cdelt))
    f.write("CDELT2  = %.9f\n" %(cdelt))
    f.write("CROTA2  = %.6f\n" %(0.0))
    f.write("EQUINOX = %d\n" %(2000))
    f.close()

    common_files["region-oversized.hdr"] = File("region-oversized.hdr")
    replica_catalog["region-oversized.hdr"] = \
            {"url": "file://" + os.getcwd() + "/data/region-oversized.hdr", "site_label": "local"}


def add_band(dax, band_id, center, degrees, survey, band, color):

    global replica_catalog

    band_id = str(band_id)

    print("\nAdding band %s (%s %s -> %s)" %(band_id, survey, band, color))

    # data find
    degrees_datafind = str(float(degrees) + 1.0)
    cmd = "mArchiveList %s %s \"%s\" %s %s data/%s-images.tbl" \
          %(survey, band, center, degrees_datafind, degrees_datafind, band_id)
    print "Running sub command: " + cmd
    if subprocess.call(cmd, shell=True) != 0:
        print "Command failed!"
        sys.exit(1)
    replica_catalog["%s-images.tbl" %(band_id)] = \
            {"url": "file://" + os.getcwd() + "/data/%s-images.tbl" %(band_id), \
             "site_label": "local"}

    # image tables
    raw_tbl = File("%s-raw.tbl" %(band_id))
    replica_catalog[raw_tbl.name] = \
            {"url": "file://" + os.getcwd() + "/data/" + raw_tbl.name, "site_label": "local"}
    projected_tbl = File("%s-projected.tbl" %(band_id))
    replica_catalog[projected_tbl.name] = \
            {"url": "file://" + os.getcwd() + "/data/" + projected_tbl.name, "site_label": "local"}
    corrected_tbl = File("%s-corrected.tbl" %(band_id))
    replica_catalog[corrected_tbl.name] = \
            {"url": "file://" + os.getcwd() + "/data/" + corrected_tbl.name, "site_label": "local"}
    cmd = "cd data && mDAGTbls %s-images.tbl region-oversized.hdr %s %s %s" \
          %(band_id, raw_tbl.name, projected_tbl.name, corrected_tbl.name)
    print "Running sub command: " + cmd
    if subprocess.call(cmd, shell=True) != 0:
        print "Command failed!"
        sys.exit(1)
    
    # diff table
    cmd = "cd data && mOverlaps %s-raw.tbl %s-diffs.tbl" \
          %(band_id, band_id)
    print "Running sub command: " + cmd
    if subprocess.call(cmd, shell=True) != 0:
        print "Command failed!"
        sys.exit(1)

    # statfile table
    t = ascii.read("data/%s-diffs.tbl" %(band_id))
    #t['stat'] = ascii.Column([])
    t['stat'] = ""
    for row in t:
        base_name = re.sub("(diff\.|\.fits.*)", "", row['diff'])
        row['stat'] = "%s-fit.%s.txt" %(band_id, base_name)
    ascii.write(t, "data/%s-stat.tbl" %(band_id), format='ipac')
    replica_catalog["%s-stat.tbl" %(band_id)] = \
            {"url": "file://" + os.getcwd() + "/data/%s-stat.tbl" %(band_id), \
             "site_label": "local"}

    # for all the input images in this band, and them to the rc, and
    # add reproject tasks
    data = ascii.read("data/%s-images.tbl" %(band_id))  
    for row in data:
        
        base_name = re.sub("\.fits.*", "", row['file'])

        # add an entry to the replica catalog
        replica_catalog[base_name + ".fits"] = {"url": row['URL'], "site_label": "ipac"}

        # projection job
        j = Job(name="mProject")
        in_fits = File(base_name + ".fits")
        projected_fits = File("p" + base_name + ".fits")
        area_fits = File("p" + base_name + "_area.fits")
        j.uses(common_files["region-oversized.hdr"], link=Link.INPUT)
        j.uses(in_fits, link=Link.INPUT)
        j.uses(projected_fits, link=Link.OUTPUT, transfer=False)
        j.uses(area_fits, link=Link.OUTPUT, transfer=False)
        j.addArguments("-X", in_fits, projected_fits, common_files["region-oversized.hdr"])
        dax.addJob(j)

    fit_txts = []
    data = ascii.read("data/%s-diffs.tbl" %(band_id))
    for row in data:
        
        base_name = re.sub("(diff\.|\.fits.*)", "", row['diff'])

        # mDiffFit job
        j = Job(name="mDiffFit")
        plus = File("p" + row['plus'])
        plus_area = File(re.sub("\.fits", "_area.fits", plus.name))
        minus = File("p" + row['minus'])
        minus_area = File(re.sub("\.fits", "_area.fits", minus.name))
        fit_txt = File("%s-fit.%s.txt" %(band_id, base_name))
        diff_fits = File("%s-diff.%s.fits" %(band_id, base_name))
        j.uses(plus, link=Link.INPUT)
        j.uses(plus_area, link=Link.INPUT)
        j.uses(minus, link=Link.INPUT)
        j.uses(minus_area, link=Link.INPUT)
        j.uses(common_files["region-oversized.hdr"], link=Link.INPUT)
        j.uses(fit_txt, link=Link.OUTPUT, transfer=False)
        #j.uses(diff_fits, link=Link.OUTPUT, transfer=True)
        j.addArguments("-s", fit_txt, plus, minus, diff_fits, common_files["region-oversized.hdr"])
        dax.addJob(j)
        fit_txts.append(fit_txt)

    # mConcatFit
    j = Job(name="mConcatFit")
    stat_tbl = File("%s-stat.tbl" %(band_id))
    j.uses(stat_tbl, link=Link.INPUT)
    j.addArguments(stat_tbl)
    fits_tbl = File("%s-fits.tbl" %(band_id))
    j.uses(fits_tbl, link=Link.OUTPUT, transfer=False)
    j.addArguments(fits_tbl)
    for fit_txt in fit_txts:
        j.uses(fit_txt, link=Link.INPUT)
    j.addArguments(".")
    dax.addJob(j)

    # mBgModel
    j = Job(name="mBgModel")
    j.addArguments("-i", "100000")
    images_tbl = File("%s-images.tbl" %(band_id))
    j.uses(images_tbl, link=Link.INPUT)
    j.addArguments(images_tbl)
    j.uses(fits_tbl, link=Link.INPUT)
    j.addArguments(fits_tbl)
    corrections_tbl = File("%s-corrections.tbl" %(band_id))
    j.uses(corrections_tbl, link=Link.OUTPUT, transfer=False)
    j.addArguments(corrections_tbl)
    dax.addJob(j)

    # mBackground
    data = ascii.read("data/%s-raw.tbl" %(band_id))  
    for row in data:
        base_name = re.sub("(diff\.|\.fits.*)", "", row['file'])

        # mBackground job
        j = Job(name="mBackground")
        projected_fits = File("p" + base_name + ".fits")
        projected_area = File("p" + base_name + "_area.fits")
        corrected_fits = File("c" + base_name + ".fits")
        corrected_area = File("c" + base_name + "_area.fits")
        j.uses(projected_fits, link=Link.INPUT)
        j.uses(projected_area, link=Link.INPUT)
        j.uses(projected_tbl, link=Link.INPUT)
        j.uses(corrections_tbl, link=Link.INPUT)
        j.uses(corrected_fits, link=Link.OUTPUT, transfer=False)
        j.uses(corrected_area, link=Link.OUTPUT, transfer=False)
        j.addArguments("-t", projected_fits, corrected_fits, projected_tbl, corrections_tbl)
        dax.addJob(j)

    # mImgtbl - we need an updated corrected images table because the pixel offsets and sizes need
    # to be exactly right and the original is only an approximation
    j = Job(name="mImgtbl")
    updated_corrected_tbl = File("%s-updated-corrected.tbl" %(band_id))
    j.uses(corrected_tbl, link=Link.INPUT)
    j.uses(updated_corrected_tbl, link=Link.OUTPUT, transfer=False)
    j.addArguments(".", "-t", corrected_tbl, updated_corrected_tbl)
    data = ascii.read("data/%s-corrected.tbl" %(band_id))  
    for row in data:
        base_name = re.sub("(diff\.|\.fits.*)", "", row['file'])
        projected_fits = File(base_name + ".fits")
        j.uses(projected_fits, link=Link.INPUT)
    dax.addJob(j)

    # mAdd
    j = Job(name="mAdd")
    mosaic_fits = File("%s-mosaic.fits" %(band_id))
    mosaic_area = File("%s-mosaic_area.fits" %(band_id))
    j.uses(updated_corrected_tbl, link=Link.INPUT)
    j.uses(common_files["region.hdr"], link=Link.INPUT)
    j.uses(mosaic_fits, link=Link.OUTPUT, transfer=True)
    j.uses(mosaic_area, link=Link.OUTPUT, transfer=True)
    j.addArguments("-e", updated_corrected_tbl, common_files["region.hdr"], mosaic_fits)
    data = ascii.read("data/%s-corrected.tbl" %(band_id))  
    for row in data:
        base_name = re.sub("(diff\.|\.fits.*)", "", row['file'])
        corrected_fits = File(base_name + ".fits")
        corrected_area = File(base_name + "_area.fits")
        j.uses(corrected_fits, link=Link.INPUT)
        j.uses(corrected_area, link=Link.INPUT)
    dax.addJob(j)

    # mJPEG - Make the JPEG for this channel
    j = Job(name="mJPEG")
    mosaic_jpg = File("%s-mosaic.jpg" %(band_id))
    j.uses(mosaic_fits, link=Link.INPUT)
    j.uses(mosaic_jpg, link=Link.OUTPUT, transfer=True)
    j.addArguments("-ct", "0", "-gray", mosaic_fits, "0s", "99.999%", "gaussian", \
                   "-out", mosaic_jpg)
    dax.addJob(j)


def color_jpg(dax, red_id, green_id, blue_id):

    global replica_catalog

    red_id = str(red_id)
    green_id = str(green_id)
    blue_id = str(blue_id)

    # mJPEG - Make the JPEG for this channel
    j = Job(name="mJPEG")
    mosaic_jpg = File("mosaic-color.jpg")
    red_fits = File("%s-mosaic.fits" %(red_id))
    green_fits = File("%s-mosaic.fits" %(green_id))
    blue_fits = File("%s-mosaic.fits" %(blue_id))
    j.uses(red_fits, link=Link.INPUT)
    j.uses(green_fits, link=Link.INPUT)
    j.uses(blue_fits, link=Link.INPUT)
    j.uses(mosaic_jpg, link=Link.OUTPUT, transfer=True)
    j.addArguments( \
            "-red", red_fits, "-1s", "99.999%", "gaussian-log", \
            "-green", green_fits, "-1s", "99.999%", "gaussian-log", \
            "-blue", blue_fits, "-1s", "99.999%", "gaussian-log", \
            "-out", mosaic_jpg)
    dax.addJob(j)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--center", action = "store", dest = "center",
                        help = "Center of the output, for example M17 or 56.5 23.75")
    parser.add_argument("--degrees", action = "store", dest = "degrees",
                        help = "Number of degrees of side of the output")
    parser.add_argument("--band", action = "append", dest = "bands",
                        help = "Band definition. Example: dss:DSS2B:red")
    args = parser.parse_args()

    if os.path.exists("data"):
        print("data/ directory already exists")
        sys.exit(1)
    os.mkdir("data")

    dax = AutoADAG("montage")

    # email notificiations for when the state of the workflow changes
    dax.invoke('all', os.getcwd() + "/email-notify.sh")

    add_transformations(dax)

    # region.hdr is the template for the ouput area
    generate_region_hdr(dax, args.center, args.degrees)

    band_id = 0
    color_band = {}
    for band_def in args.bands:
        band_id += 1
        (survey, band, color) = band_def.split(":")
        add_band(dax, band_id, args.center, args.degrees, survey, band, color)
        color_band[color] = band_id

    # if we have 3 bands in red, blue, green, try to create a color jpeg
    if 'red' in color_band and 'green' in color_band and 'blue' in color_band:
        color_jpg(dax, color_band['red'], color_band['green'], color_band['blue'])

    # write out the replica catalog
    fd = open("data/rc.txt", "w")
    for lfn, data in replica_catalog.iteritems():
        fd.write("%s \"%s\"  pool=\"%s\"\n" %(lfn, data['url'], data['site_label']))
    fd.close()

    fd = open("data/montage.dax", "w")
    dax.writeXML(fd)
    fd.close()


if __name__ == "__main__":
    main()


