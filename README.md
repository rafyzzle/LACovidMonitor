# LACovidMonitor

**NOTE: This tool is not at all affiliated with Los Angeles County**

Simple independent tool to visualize COVID hospitalization, tests and death rates per
LA County Public Health reports.

To include some metrics not immediately available on http://dashboard.publichealth.lacounty.gov/covid19_surveillance_dashboard/
  - \# of NEW Daily Hospitalizations
  - \# of Hospitalizations (Ever) 
  - 7-day moving averages and medians
  - \# Currently Hospitalized   (this is a TODO.. need a data source..)
  - \# of Test Cases w/ Results


Usage: 
    Import the module and use the run() routine.  Make sure useCached is False
    if you want it to grab latest reports from LACPH

