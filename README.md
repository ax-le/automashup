# Automashup

Automashup is a Python application that allows you to generate a mashup from several songs :
![](https://github.com/huyhoangpjn/AutoMashup/blob/main/app.gif)

## Installation

We strongly recommand the use of a Python 3.10 environment with a Conda environment.

> pip3 install -r requirements.txt

NATTEN version 0.15.1

> pip install natten==0.15.1+torch200cu117 -f https://shi-labs.com/natten/wheels

Pyrubberband-cli

> sudo apt install rubberband-cli

To install All-In-One Music Structure Analyzer: https://github.com/mir-aidj/all-in-one/tree/main (LINUX, MACOS RECOMMANDED!)

### Launch the app

> cd ./automashup-app

> streamlit run app.py

## Other

To install and test DMC on your own: https://github.com/csteinmetz1/automix-toolkit (clone + set up (modify sklearn --> scikit-learn in the setup.py) and test directly on your machine, dont forget to modify the paths)

## Docker Image

We have a docker image of the automashup app, it's only been tested on Linux :
https://hub.docker.com/r/gaubiche/automashup/

## Adding Mashup Methods

The aim of this interface is to present multiple mashup technics.

You can add some to the application by creating a mashup function in the file /automashup-app/mashup.py and then modifying a little bit the file automashup-app/app.py

If you want to experiment around new mashup methods, you can use the /automashup-notebook/notebook.ipynb file. It shows an example of a working mashup method