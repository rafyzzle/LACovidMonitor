# LACovidMonitor

Simple independent tool to visualize COVID hospitalization, tests and death rates per
LA County Public Health reports.

  - \# of NEW Daily Hospitalizations
  - \# of Hospitalizations (Ever) 
  - 7-day moving averages and medians
  - \# Currently Hospitalized   (this is a TODO.. need a data source..)
  - \# of Test Cases w/ Results

Visit http://dashboard.publichealth.lacounty.gov/covid19_surveillance_dashboard/
for LA County's official dashboard w/ additional visualizations.

Note that I wrote this when the above metrics were not immidately available on 
the dashboard.  As of now, May 17, a little over 2 weeks after the birth of 
this tool, they are now also easily displayable along with more info.

As such, lifetime of this little script has come to an end.

Usage: 
    Import the module and use the run() routine.  Make sure useCached is False
    if you want it to grab latest reports from LACPH

![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f9.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f10.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f7.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f6.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f5.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f4.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f3.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f2.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f1.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f0.png)
![](https://github.com/rafyzzle/LACovidMonitor/blob/master/plots/June_23_2020/f8.png)
