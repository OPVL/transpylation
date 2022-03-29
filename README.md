# transpylation
a very shit but effective tool for finding unused translations inside a codebase


## requirements

* python 3.6+
* pip


## usage
1. clone or copy the scrape.py in to the root of your project directory
2. adjust the settings in scrape.ini 
3. run the program

all translation files must be in valid JSON format. it's not clever enough to work with anything else

## future plans

currently exploring how to use as github action step / CI step
support for language files other than json(? if requested, only have use for JSON)
package as pypackage can be installed using pip
parse commandline arguments
support for different configs

### tool in action
in this video it is evaluating ~230 translation strings in 5 languages in a codebase of around ~500 files
it takes around 2 minutes to completely evaluate all translation files (not making changes)

[![IMAGE ALT TEXT](http://img.youtube.com/vi/cVXKPRFz5J8/0.jpg)](https://www.youtube.com/watch?v=cVXKPRFz5J8 "Python translation tool")

running in debug is a lot slower. same exact pass but we're slamming the log buffer
[![IMAGE ALT TEXT](http://img.youtube.com/vi/f2EwO0z8otw/0.jpg)](https://youtu.be/f2EwO0z8otw "Python translation tool [debug mode]")
