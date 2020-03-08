# NHSD-Test
This example is for test purposes only. NHS Digital have invested in some tools to capture deployment data. The purpose of collecting the data is to analyse deployment data between projects as a way of optimising our continuous delivery approach.


The script makes use of the following packages for this example:
> json - Module to read data from the json file

> datetime - Module to get/convert to datetime in python

> csv - Module to create and modify csv files

> statistics - Module to carry out quick calculations based on statistics



Quick start
==============

Pre-Requisites
=================
• You need to have Python 3.6 or above installed



Steps to run application from command line
=================
After downloading and unzipping the folder, you need to:

• On your command line, go to the folder where you have unzipped this project (should be a folder named `nhsd-test`)

• You should see a python script called `app.py` in the root of the folder

• Run the python script by running this command - `python app.py`

• If the run was successful, you should see the 3 reports generated in the `output` folder

• NOTE: If you wish to run it from via the python repl, you can do that by typing `python` ,from inside the same folder, on your cmd line and after the repl is open, 
you can run the below steps: 
    `>>> import app`
    `>>> app.generate_reports()` (which should give you the same outcome in the `output` folder)
    `>>> exit()`


Steps to run tests from command line
=================
• On your command line, go to the folder where you have unzipped this project

• Run the python test script by running this command - `python -m unit_tests.tests`
