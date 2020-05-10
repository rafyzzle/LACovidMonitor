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
  --> # of NEW Daily Hospitalizations
  --> # of Hospitalizations (Ever)
  --> # Currently Hospitalized
  --> # of Test Cases w/ Results
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
CNX_TIMEOUT_SEC = 5 # Note, as sometimes server won't respond... just try again later

"""
Get reports from local cache
"""
def getReportsCached(cacheDir = DEFAULT_CACHE_DIR):
    files = os.listdir(cacheDir)
    files.sort()
    reportDatas = []
    
    print(f"Reading cached reports from {cacheDir}")
    
    for file in files:
        if re.match(r"report[0-9]{3}.html", file):
            fid = open(cacheDir + '/' + file, 'r')
            reportDatas += [fid.read(),]
            fid.close()    
    return reportDatas
    
"""
Pull reports from LADPH website, cache if requested
"""
def getReports(cache = False, cacheDir = DEFAULT_CACHE_DIR):
    if cache and not os.path.exists(cacheDir):
        os.mkdir(cacheDir)
        
    print(f"Pulling reports from {SERVER_URL}, saveReportsToCache:{cache}")
    cnx = http.client.HTTPConnection(SERVER_URL, timeout=CNX_TIMEOUT_SEC)
    
    cnx.request("GET", URL_MAIN)
    rsp = cnx.getresponse()
    print(f"Grabbing list of reports, HTTP Response: {rsp.status} {rsp.reason}")
    if (rsp.status != 200):
        return
    
    mainReportPage = rsp.read().decode('utf-8')    
    reportURLs = re.findall(r'((Los Angeles County Announces.*?)|(\(COVID-19\) Advisory.*?))action="(?P<z>.*?)">', mainReportPage, re.S)
    reportURLs = [z[3] for z in reportURLs] # get link
    
    repNum = 0
    reportDatas = []
    for url in reportURLs[::-1]:
        cnx.request("POST", URL_ROOT + url)
        rsp = cnx.getresponse()
        print(f"Report #{repNum:03d}, HTTP Response: {rsp.status} {rsp.reason}")
        if (rsp.status != 200):
            return
        
        reportData = rsp.read().decode('utf-8')
        
        reportDatas += [reportData,]
        
        if cache:
            fn = f"report{repNum:03d}.html"
            repNum = repNum + 1
            fid = open(f"{cacheDir}/{fn}", 'w')
            fid.write(reportData)
            fid.close()
            
    return reportDatas

"""
Parse reports
returns a list of dictionaries
 currently,
  # new deaths, # total hospitalizations, report date, 
 ... will do testing reults next
 ... need to fix date (the first few report dates may be off) 
"""
def parseReports(reports):
    parsed = []
    repNum = 0
    for report in reports:

        # Get date, (this doesn't always work fully yet)
        match = re.search(r'(?P<z>[\w]+[\s][0-9]{2}, 2020)', report)
        rDate = match[0] if match else '???'
        
        # Get # Hospitalized (Cumalative)
        match = re.search(r'Hospitalized \(Ever\)[\s]*(?P<numb>[0-9]+)', report)
        rHospitalized = int(match[1]) if match else 0

        # Get # passed away from COVID for this day
        z = {'One':1,'Two':2,'Three':3,'Four':4,'Five':5,'Six':6,'Seven':7,'Eight':8,'Nine':9}
        match = re.search(r'([0-9]+|One|Two|Three|Four|Five|Six|Seven|Eight|Nine) New Death', report)
        if match:
            try:
                rDeaths = int(match[1])
            except:
                rDeaths = z[match[1]]
        else:
            rDeaths = 0
        
        # Get # of available test results. (Testing Capacity)
        match = re.search(r'Testing[\s]+capacity .*? (?P<numRes>[0-9,]+)', report)
        rTestsWithResults = 0
        if match:
            rTestsWithResults = int(match[1].replace(',',''))

        # Get # of new positives.
        match = re.search(r'(?P<z>[0-9]+)[\s]New Cases', report)
        rNewCases = 0
        if match:
            rNewCases = int(match[1].replace(',',''))
                
        parsed.append({'repNum': repNum, 
                       'date': rDate, 
                       'tHosp': rHospitalized, 
                       'dDeaths': rDeaths,
                       'dNewCases' : rNewCases,
                       'tTestsWithResults': rTestsWithResults})
        repNum = repNum + 1
        
    return parsed

"""
Running average and median
"""
def simpWinFilt(arr, winSz=7):
    winSzH = int(winSz/2)
    y = np.ndarray(len(arr)-winSz + 1)
    yM = np.ndarray(len(arr)-winSz + 1)
    for i in np.arange(winSzH,len(arr)-winSzH):
        y[i-winSzH] = np.sum(arr[i-winSzH:i+winSzH+1]) / winSz
        yM[i-winSzH] = np.median(arr[i-winSzH:i+winSzH+1])
    
    return y,yM

"""
Make plots.. I'll doc this later.
"""
def makePlots(parsedReports, saveFigs=False):
    
    pR = parsedReports
    latest = pR[-1]["date"]
    # Total hospitalizations
    f0 = plt.figure()
    numHospitalized = np.array([p['tHosp'] for p in pR])
    plt.plot(numHospitalized, 'r.')
    plt.xlabel(f'Days since first hospitalization report (Last Upd {latest})')
    plt.ylabel('# Ever Hospitalized (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    
    # New hospitalizations with 7-day running median
    f1 = plt.figure()
    newHospitalized = numHospitalized[1:] - numHospitalized[0:-1]
    plt.plot(newHospitalized, 'r.')
    plt.xlabel(f'Days since first hospitalization report (Last Upd {latest})')
    plt.ylabel('# New Hospitalizations (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    winSz = 7
    winSzH = int(winSz/2)
    [newHospAvg, newHospMed] = simpWinFilt(newHospitalized, winSz)
    plt.plot(np.arange(winSzH,len(newHospitalized)-winSzH), newHospMed, 'b')

    # New hospitalizations with 7-day running average    
    f2 = plt.figure()
    plt.plot(newHospitalized, 'r.')
    plt.xlabel(f'Days since first hospitalization report (Last Upd {latest})')
    plt.ylabel('# New Hospitalizations (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.plot(np.arange(winSzH,len(newHospitalized)-winSzH), newHospAvg, 'b')
    
    # Number of people passed away (per day) w/ 7-day running average
    f3 = plt.figure()
    numberDied = [p['dDeaths'] for p in pR]
    plt.plot(numberDied, 'r.', label='# newly deceased')
    plt.xlabel(f'Days')
    plt.ylabel('# Newly deceased')
    plt.title('LA County (Newly deceased)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    [numberDiedAvg, numberDiedMed] = simpWinFilt(numberDied, winSz)
    plt.plot(np.arange(winSzH,len(numberDied)-winSzH), numberDiedAvg, 'b',
             label='7-day average')
    plt.legend()

    # Number of people passed away (per day) w/ 7-day running median
    f4 = plt.figure()
    plt.plot(numberDied, 'r.', label='# newly deceased')
    plt.xlabel(f'Days')
    plt.ylabel('# Newly deceased')
    plt.title('LA County (Newly deceased)')
    plt.grid('on')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.plot(np.arange(winSzH,len(numberDied)-winSzH), numberDiedMed, 'b',
             label='7-day median')
    plt.legend()
        
    f5 = plt.figure()
    totResults = [p['tTestsWithResults'] for p in pR]
    totResults = np.array(totResults)
    plt.plot(totResults, 'r.')
    plt.xlabel(f'Days')
    plt.ylabel('Total # of Tests w/ Results')
    plt.title('Total # of Tests w/ Results')
    plt.grid('on')
    
    f6 = plt.figure()
    newResults = totResults[1:]-totResults[0:-1]
    newResults[newResults > 25000] = 0 # Remove initial report of tests...
    [newResultsAvg, newResultsMed] = simpWinFilt(newResults, winSz)
    plt.plot(np.arange(winSzH,len(newResults)-winSzH), newResultsMed, 'b')
    plt.plot(newResults, 'r.')
    plt.xlabel(f'Days')
    plt.ylabel('Newly available test results (est)')
    plt.title('Newly available test results (est)')
    plt.grid('on')
    
    f7 = plt.figure()
    newResults = totResults[1:]-totResults[0:-1]
    newCases = [p['dNewCases'] for p in pR]
    
    newCases = np.array(newCases)
    newCasesTot = np.cumsum(newCases)
    plt.plot(totResults, 'r.', label='# Available Test Results')
    plt.plot(newCasesTot, 'b.', label='# COVID Positive')
    plt.xlabel(f'Days (Last Upd {latest})')
    plt.grid('on')
    plt.legend()
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    
    
    if saveFigs:
        newDir = latest.replace(" ","_").replace(",","")
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
        f5.savefig(os.path.join(saveDir, 'f5.png'))
        f6.savefig(os.path.join(saveDir, 'f6.png')) 
        f7.savefig(os.path.join(saveDir, 'f7.png')) 

"""
Main routine, will doc later.
"""
def run(saveFigs=False, useCached=True):
    runRes = None
    
    if useCached:
        # Use local version of reports
        reports = getReportsCached()
    else:
        # Pull data from LA County Public Health and update our cache
        updateCache = True 
        reports = getReports(updateCache)
    
    if reports:
        # Parse the daily reports
        parsed = parseReports(reports)
        
        # Make our plots
        makePlots(parsed, saveFigs=saveFigs)
        
        runRes = parsed
    else:
        print("Unable to access reports.")
        
    return runRes

if __name__ == "__main__":
    if (os.path.exists(DEFAULT_CACHE_DIR)):
        run()
    else:
        run(useCached=False)