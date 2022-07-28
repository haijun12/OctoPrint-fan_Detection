Fan Speed Attack Detection Plugin
=========================

A plugin that monitors fan speed changes sent through GCode Commands
and Displays the status of the printing quality given any fan speed changes

![Screenshot] (https://github.com/haijun12/OctoPrint-fan_Detection/blob/main/screenshots/green_status.png)
![Screenshot] (https://github.com/haijun12/OctoPrint-fan_Detection/blob/main/screenshots/orange_status.png)
![Screenshot] (https://github.com/haijun12/OctoPrint-fan_Detection/blob/main/screenshots/red_status.png)

Green Status = Fan Speed has not been changed from initial print
Orange Status = Fan Speed has been changed but printing quality is still high
Red Status = Fan speed was attempted to be changed but because the printing quality is low, it is not used

## Features

* Reads Initial Printing Parameters once a Print is started:
    * Fan Speed (FS)
    * Infill Density (ID)
    * Layer Height (LT)
* Predicts the surface roughness through the three parameters with a Neural Network Model
* Classifes the initial print as a high or low quality print with Clustering Model
* Monitors Printer for any Fan Speed changes through the GCode M106 Command
* Given the new fan speed and initial print state:
    * High quality initial print = high tolerance 
    * Low Quality Initial Print = low tolerance
        * New Fan speed is compared to high tolerance or low tolerance
            * Orange Status if print is still high quality
            * Red Status if print is low quality due to FS 

## Specific Requirements

* Given this was only a 10 week Research Project, there are certain limitations to this plugin:
    * Only works with Prusa Sliced GCode Files or similarly formatted GCode Files (See Process_GCode in __init__.py)
    * Prediction Models are more accurate in these specific printing parameters:
        * FS: 0% <= x <= 100%
        * ID: 20% <= x <= 80%
        * FS: .1mm <= x <= .3 mm
    * GCode File must be under /home/pi/Downloads folder and must match SD Card folder name exactly (case sensitive)

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager) or manually using this URL:

    https://github.com/haijun12/OctoPrint-fan_Detection/archive/master.zip

## Configuration

* For configuration help, please visit the [wiki](https://github.com/j7126/OctoPrint-Dashboard/wiki).

## Credits
    * Inspired by OctoPrint Dashboard: https://github.com/j7126/OctoPrint-Dashboard
    * Created by haijun12
    * Mentors: Ismail Fidan, Zhicheng Zhang, and Orkhan Huseynov