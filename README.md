# LACovidMonitor

**** NOTE: This tool is not at all affiliated with Los Angeles County ****


Simple independent tool to visualize COVID hospitalization, tests and death rates per
LA County Public Health reports.

Yes, as of May 3, they've got a fancy Surveillance Dashboard the public can use, but it 
doesnt really have the metrics I'm interested in...
  --> # of NEW Daily Hospitalizations [DONE]
  --> # of Hospitalizations (Ever)    [DONE]
  --> # Currently Hospitalized <--- still looking for a good source for this #'
  --> # of Test Cases w/ Results      [TODO]
  --> 7-day moving averages and medians


Usage: 
    Import the module and use the run() routine.  Make sure useCached is False
    if you want it to grab latest reports from LACPH

