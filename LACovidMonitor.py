#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  3 17:17:54 2020

@author: rafaelnuguid

Simple independent tool to visualize COVID hospitalization, tests and death rates per
LA County Public Health reports.
  
  --> # of NEW Daily Hospitalizations
  --> # of Hospitalizations (Ever)
  --> # Currently Hospitalized
  --> # of Test Cases w/ Results
  --> 7-day moving averages and medians

Visit http://dashboard.publichealth.lacounty.gov/covid19_surveillance_dashboard/
for LA County's official dashboard w/ additional visualizations.

Note that I wrote this when the above metrics were not immidately available on 
the dashboard.  As of now, May 17, a little over 2 weeks after the birth of 
this tool, they are now also easily displayable along with more info.

As such, lifetime of this little script has come to an end.


Usage: 
    Import the module and use the run() routine.  Make sure useCached is False
    if you want it to grab latest reports from LACPH

"""

import numpy as np
import matplotlib.pyplot as plt

import os
import http
import re
import datetime

SERVER_URL = "publichealth.lacounty.gov"
URL_ROOT = "http://publichealth.lacounty.gov/phcommon/public/media/"
URL_MAIN = URL_ROOT + "mediaCOVIDdisplay.cfm?unit=media&ou=ph&prog=media"
DEFAULT_CACHE_DIR = "./cache/"
DEFAULT_FIG_DIR = "./plots/"
CNX_TIMEOUT_SEC = 5 # Note, as sometimes server won't respond... just try again later


def getReportsCached(cacheDir = DEFAULT_CACHE_DIR):
    """ Get reports from local cache """
    
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
    
def getReports(cache = False, cacheDir = DEFAULT_CACHE_DIR, onlyNew = False):
    """ Get reports from LADPH, cache if requested """
    
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
    
    if onlyNew:     
        print("Only looking for new reports...")
        reports = getReportsCached(cacheDir)
        if len(reportURLs) > len(reports):
            print(f"Found new reports!")
            repNum = len(reports)
            reportDatas = reports
            for url in reportURLs[-len(reports)-1::-1]:
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
        else:
            print("No new reports, only using cached..")
            reportDatas = reports
            
    else:
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

def parseReports(reports):
    """
    Parse reports, (list of html reports...)
    Will extract data using some ad-hoc regexs..
    Returns a list of dictionaries, (1 elem per report)
    """
    parsed = []
    repNum = 0
    for report in reports:

        # Get date
        match = re.search(r'(?P<z>[\w]+[\s][0-9]{2}, 2020)', report)
        rDate = datetime.datetime.strptime(match[0], "%B %d, %Y")
        
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
        match = re.search(r'(?P<z>[0-9,]+)[\s]New Cases', report)
        rNewCases = int(match[1].replace(',','') if match is not None else 0)
            
        # Get # currently hospitalized (they started reporting this on May 12!)
        match = re.search(r'(?P<z>[0-9,]+)[\s]+people[\s]+who[\s]+are[\s]+currently[\s]+hospitalized', report)
        rCurrHosp = int(match[1].replace(',','')) if match is not None else 0
            
        parsed.append({'repNum': repNum, 
                       'date': rDate, 
                       'tHosp': rHospitalized, 
                       'dDeaths': rDeaths,
                       'dNewCases' : rNewCases,
                       'tTestsWithResults': rTestsWithResults,
                       'dCurrHosp': rCurrHosp})
        
        repNum = repNum + 1
        
    return parsed

def simpWinFilt(arr, winSz=7):
    """ Running avg and median """
    winSzH = int(winSz/2)
    y = np.ndarray(len(arr)-winSz + 1)
    yM = np.ndarray(len(arr)-winSz + 1)
    for i in np.arange(winSzH,len(arr)-winSzH):
        y[i-winSzH] = np.sum(arr[i-winSzH:i+winSzH+1]) / winSz
        yM[i-winSzH] = np.median(arr[i-winSzH:i+winSzH+1])
    
    return y,yM

def makePlots(parsedReports, saveFigs=False):
    """ Generate some ad-hoc plots from list of parsed reports """
    
    pR = parsedReports
    dates = np.array([d["date"] for d in pR])
    
    latest = pR[-1]["date"].strftime('%B %d, %Y')
    
    # Total hospitalizations
    f0 = plt.figure()
    numHospitalized = np.array([p['tHosp'] for p in pR])
    plt.plot(dates, numHospitalized, 'r.')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.ylabel('# Ever Hospitalized (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    #plt.xlim(left=0)
    f0.autofmt_xdate()
    plt.ylim(bottom=0)
    
    # New hospitalizations with 7-day running median
    f1 = plt.figure()
    newHospitalized = numHospitalized[1:] - numHospitalized[0:-1]
    plt.plot(dates[1:], newHospitalized, 'r.')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.ylabel('# New Hospitalizations (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    plt.ylim(bottom=0)
    winSz = 7
    winSzH = int(winSz/2)
    [newHospAvg, newHospMed] = simpWinFilt(newHospitalized, winSz)
    plt.plot(dates[np.arange(winSzH,len(newHospitalized)-winSzH, dtype=int)], newHospMed, 'b')
    f1.autofmt_xdate()
    
    # New hospitalizations with 7-day running average    
    f2 = plt.figure()
    plt.plot(dates[1:], newHospitalized, 'r.')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.ylabel('# New Hospitalizations (COVID-19)')
    plt.title('LA County (Hospitalizations)')
    plt.grid('on')
    plt.ylim(bottom=0)
    plt.plot(dates[np.arange(winSzH,len(newHospitalized)-winSzH)], newHospAvg, 'b')
    f2.autofmt_xdate()
    
    # Number of people passed away (per day) w/ 7-day running average
    f3 = plt.figure()
    numberDied = [p['dDeaths'] for p in pR]
    plt.plot(dates, numberDied, 'r.', label='# newly deceased')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.ylabel('# Newly deceased')
    plt.title('LA County (Newly deceased)')
    plt.grid('on')
    plt.ylim(bottom=0)
    [numberDiedAvg, numberDiedMed] = simpWinFilt(numberDied, winSz)
    plt.plot(dates[np.arange(winSzH,len(numberDied)-winSzH)], numberDiedAvg, 'b',
             label='7-day average')
    plt.legend()
    f3.autofmt_xdate()

    # Number of people passed away (per day) w/ 7-day running median
    f4 = plt.figure()
    plt.plot(dates, numberDied, 'r.', label='# newly deceased')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.ylabel('# Newly deceased')
    plt.title('LA County (Newly deceased)')
    plt.grid('on')
    plt.ylim(bottom=0)
    plt.plot(dates[np.arange(winSzH,len(numberDied)-winSzH)], numberDiedMed, 'b',
             label='7-day median')
    plt.legend()
    f4.autofmt_xdate()  
    
    f5 = plt.figure()
    totResults = [p['tTestsWithResults'] for p in pR]
    totResults = np.array(totResults)
    plt.plot(dates, totResults, 'r.')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.ylabel('Total # of Tests w/ Results')
    plt.title('Total # of Tests w/ Results')
    plt.grid('on')
    plt.xlim(left=datetime.datetime(2020, 4, 1))
    f5.autofmt_xdate()
    
    f6 = plt.figure()
    newResults = totResults[1:]-totResults[0:-1]
    newResults[newResults < 0] = 0
    [newResultsAvg, newResultsMed] = simpWinFilt(newResults, winSz)
    plt.plot(dates[np.arange(winSzH,len(newResults)-winSzH)], newResultsMed, 'b')
    plt.plot(dates[1:], newResults, 'r.')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.ylabel('Newly available test results (est)')
    plt.title('Newly available test results (est)')
    plt.grid('on')
    plt.xlim(left=datetime.datetime(2020, 4, 1))
    f6.autofmt_xdate()
    
    f7 = plt.figure()
    newResults = totResults[1:]-totResults[0:-1]
    newCases = [p['dNewCases'] for p in pR]
    
    newCases = np.array(newCases)
    newCasesTot = np.cumsum(newCases)
    plt.plot(dates, totResults, 'r.', label='# Available Test Results')
    plt.plot(dates, newCasesTot, 'b.', label='# COVID Positive')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.grid('on')
    plt.legend()
    plt.xlim(left=datetime.datetime(2020, 4, 1))
    plt.ylim(bottom=0)
    f7.autofmt_xdate()
    
    f8 = plt.figure()
    currHosp = np.array([p['dCurrHosp'] for p in pR])
    plt.plot(dates, currHosp, 'ro--', label='# Currently Hospitalized')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.grid('on')
    plt.legend()
    plt.title('# Currently Hospitalized')
    plt.xlim(left=datetime.datetime(2020,5,12))
    plt.ylim(bottom=0)
    f8.autofmt_xdate()
    
    f9 = plt.figure()
    dPosRate = newCases[1:] / newResults
    winSz = 7
    winSzH = int(winSz/2)
    [dPosRateAvg, dPosRateMed] = simpWinFilt(dPosRate, winSz)
    plt.plot(dates[np.arange(winSzH,len(dPosRate)-winSzH)], dPosRateAvg*100, 'ro--', label='7-day Positivity Rate')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.grid('on')
    plt.legend()
    plt.title('7-day COVID positivity rate')
    #plt.xlim(left=datetime.datetime(2020,4,1))
    plt.ylim(bottom=0)
    f9.autofmt_xdate()
    
    f10 = plt.figure()
    winSz = 15
    winSzH = int(winSz/2)
    [dCasesInfectAvg, dCasesInfectMed] = simpWinFilt(newCases, winSz)
    fudgeFactor = 5 # this is super rough
    lacPopulation = 10000000
    dCasesInfectRateEst = dCasesInfectAvg * winSz * fudgeFactor / lacPopulation * 100
    plt.plot(dates[np.arange(winSz-1,len(newCases))], dCasesInfectRateEst, 'ro--', label='% Infected (cases last 2 weeks * 5/10mil)')
    plt.xlabel(f'Date (Last Pt {latest})')
    plt.grid('on')
    plt.legend()
    plt.title('Rough est, % LAC infected (2-week case count * ff=5 / pop=10mil)')
    # Because i'm assuming constant fudge, this would be very misleading otherwise
    # as I'm pretty sure fudge factor earlier is much higher.. perhaps could
    # tie in with positivity rate or # of tests conducted... but that gets
    # too out there..
    plt.xlim(left=datetime.datetime(2020,6,1)) 
    plt.ylim(bottom=0)
    f10.autofmt_xdate()
    
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
        f8.savefig(os.path.join(saveDir, 'f8.png'))
        f9.savefig(os.path.join(saveDir, 'f9.png')) 
        f10.savefig(os.path.join(saveDir, 'f10.png')) 

def run(saveFigs=False, useCached=True, onlyNew=True):
    """ Main routine """
    runRes = None
    
    if useCached:
        # Use local version of reports
        reports = getReportsCached()
    else:
        # Pull data from LA County Public Health and update our cache
        updateCache = True 
        reports = getReports(updateCache, onlyNew=onlyNew)
    
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