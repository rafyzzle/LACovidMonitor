#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  3 17:17:54 2020

@author: rafaelnuguid
"""

import numpy as np
import matplotlib.pyplot as plt

import os
import http
import re

"""
**** NOTE: This tool is not at all affiliated with Los Angeles County ****


Simple independent tool to visualize COVID hospitalization, tests and death rates per
LA County Public Health reports.

To include some metrics not immediately available on http://dashboard.publichealth.lacounty.gov/covid19_surveillance_dashboard/
  --> # of NEW Daily Hospitalizations [DONE]
  --> # of Hospitalizations (Ever)    [DONE]
  --> # Currently Hospitalized <--- still looking for a good source for this #'
  --> # of Test Cases w/ Results      [TODO]
  --> 7-day moving averages and medians


Usage: 
    Import the module and use the run() routine.  Make sure useCached is False
    if you want it to grab latest reports from LACPH

"""

SERVER_URL = "publichealth.lacounty.gov"
URL_ROOT = "http://publichealth.lacounty.gov/phcommon/public/media/"
URL_MAIN = URL_ROOT + "mediaCOVIDdisplay.cfm?unit=media&ou=ph&prog=media"
DEFAULT_CACHE_DIR = "./cache/"
DEFAULT_FIG_DIR = "./plots/"

def getReportsCached(cacheDir = DEFAULT_CACHE_DIR):
    files = os.listdir(cacheDir)
    files.sort()
    reportDatas = []
    for file in files:
        if re.match(r"report[0-9]{3}", file):
            fid = open(cacheDir + '/' + file, 'r')
            reportDatas += [fid.read(),]
            fid.close()    
    return reportDatas

# I'm not sure why I made this one..
def getMainReportPageCached(cacheDir = DEFAULT_CACHE_DIR):
    fid = open(f"{cacheDir}/main", 'r')
    mainReportPage = fid.read()
    fid.close()    
    return mainReportPage

def getMainReportPage(cache = False, cacheDir = DEFAULT_CACHE_DIR):
    if cache and not os.path.exists(cacheDir):
        os.mkdir(cacheDir)
        
    cnx = http.client.HTTPConnection(SERVER_URL)
    cnx.request("GET", URL_MAIN)
    rsp = cnx.getresponse()
    
    mainReportPage = repr(rsp.read())
    
    if cache:
        fn = f"main"
        fid = open(f"{cacheDir}/{fn}", 'w')
        fid.write(mainReportPage)
        fid.close()
    
    return mainReportPage
    
def getReports(mainReportPage, cache = False, cacheDir = DEFAULT_CACHE_DIR):
    if cache and not os.path.exists(cacheDir):
        os.mkdir(cacheDir)
        
    cnx = http.client.HTTPConnection(SERVER_URL)
    
    reportURLs = re.findall(r'Los Angeles County Announces.*?action="(?P<z>.*?)">', 
               mainReportPage)
    repNum = 0
    reportDatas = []
    for url in reportURLs[::-1]:
        cnx.request("POST", URL_ROOT + url)
        rsp = cnx.getresponse()
        reportData = repr(rsp.read())
        
        reportDatas += [reportData,]
        
        if cache:
            fn = f"report{repNum:03d}"
            repNum = repNum + 1
            fid = open(f"{cacheDir}/{fn}", 'w')
            fid.write(reportData)
            fid.close()
            
    return reportDatas

def run(saveFigs=False, useCached=True):
    if useCached:
        reports = getReportsCached()
    else:
        updateCache = True # Why not... should always update cache if we are checking the server!
        
        mainReportPg = getMainReportPage(updateCache)
        reports = getReports(mainReportPg, updateCache)
        
    # Now get the data.
    numberHospitalized = np.array([])
    numberDied = np.ndarray([0])
    dates = []
    
    z = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5,'Six':6,'Seven':7,'Eight':8,'Nine':9}

    for report in reports:

        mats = re.findall(r'Hospitalized \(Ever\)\\t(?P<numb>[0-9]+)', report)
        if mats:
            numberHospitalized = np.append(numberHospitalized, int(mats[0]))
        else:
            numberHospitalized = np.append(numberHospitalized, 0)
            
        # Oddly, this doesn't detect some of the earlier dates, need to investigaet.
        mats = re.findall(r't(?P<z>[\w]+[\s][0-9]{2}, 2020)', report)
        if mats:
            dates += [mats[0]]
        else:
            dates += ['???',]
        
        mats = re.findall(r'([0-9]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine) New Death', report)
        if mats:
            try:
                numberDied = np.append(numberDied, int(mats[0]))
            except:
                numberDied = np.append(numberDied, z[mats[0]])
        else:
            numberDied = np.append(numberDied, 0)
        
        # Hrm... lets look into this.
        mats = re.findall(r'testing results [\w\s,%]+', report)
        if mats:
            print(mats)  
        else:
            print('No results.')
        
    f0 = plt.figure()
    plt.plot(numberHospitalized, 'r.')
    plt.xlabel(f'Days since first hospitalization report (Last Upd {dates[-1]})')
    plt.ylabel('# Ever Hospitalized (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    
    f1 = plt.figure()
    plt.plot(numberHospitalized[1:] - numberHospitalized[0:-1], 'r.')
    plt.xlabel(f'Days since first hospitalization report (Last Upd {dates[-1]})')
    plt.ylabel('# New Hospitalizations (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    
    dH = numberHospitalized[1:] - numberHospitalized[0:-1]
    winSz = 7
    winSzH = int(winSz/2)
    y = np.ndarray(len(dH)-winSz + 1)
    yM = np.ndarray(len(dH)-winSz + 1)
    for i in np.arange(winSzH,len(dH)-winSzH):
        y[i-winSzH] = np.sum(dH[i-winSzH:i+winSzH+1]) / winSz
        yM[i-winSzH] = np.median(dH[i-winSzH:i+winSzH+1])
    plt.plot(np.arange(winSzH,len(dH)-winSzH), y, 'b')
    
    f2 = plt.figure()
    plt.plot(numberHospitalized[1:] - numberHospitalized[0:-1], 'r.')
    plt.xlabel(f'Days since first hospitalization report (Last Upd {dates[-1]})')
    plt.ylabel('# New Hospitalizations (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.plot(np.arange(winSzH,len(dH)-winSzH), yM, 'g')
    
    dH = numberDied
    winSz = 7
    winSzH = int(winSz/2)
    y = np.ndarray(len(dH)-winSz + 1)
    yM = np.ndarray(len(dH)-winSz + 1)
    for i in np.arange(winSzH,len(dH)-winSzH):
        y[i-winSzH] = np.sum(dH[i-winSzH:i+winSzH+1]) / winSz
        yM[i-winSzH] = np.median(dH[i-winSzH:i+winSzH+1])
    
    f3 = plt.figure()
    plt.plot(numberDied, 'r.')
    plt.xlabel(f'Days')
    plt.ylabel('# Deaths')
    plt.title('LA County (Deaths)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.plot(np.arange(winSzH,len(dH)-winSzH), y, 'b')


    f4 = plt.figure()
    plt.plot(numberDied, 'r.')
    plt.xlabel(f'Days')
    plt.ylabel('# Deaths')
    plt.title('LA County (Deaths)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.plot(np.arange(winSzH,len(dH)-winSzH), yM, 'b')
        
    if saveFigs:
        newDir = dates[-1].replace(" ","_").replace(",","")
        if not os.path.exists(DEFAULT_FIG_DIR):
            os.mkdir(DEFAULT_FIG_DIR)
            
        saveDir = os.path.join(DEFAULT_FIG_DIR,newDir)
        if not os.path.exists(saveDir):
            os.mkdir(saveDir)
            
        f0.savefig(os.path.join(saveDir, 'f0.png'))
        f1.savefig(os.path.join(saveDir, 'f1.png'))
        f2.savefig(os.path.join(saveDir, 'f2.png'))
        f3.savefig(os.path.join(saveDir, 'f3.png'))
        f4.savefig(os.path.join(saveDir, 'f4.png'))

    return

if __name__ == "__main__":
    if (os.path.exists(DEFAULT_CACHE_DIR)):
        run()
    else:
        run(useCached=False)