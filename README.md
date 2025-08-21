# Automashup: Automatic Music Mashups Creation

Hi, and welcome to this GitHub repository, which is the companion repository for the article "Automashup: Automatic Music Mashups Creation," published at the GRETSI 2025 conference. The paper is accessible here: https://hal.science/hal-05191030/document.

This repository contains two sub-repositories:
- "app - backend and frontend," that contains the AutoMashup core functions, including the Mashup creation process and the GUI webpage,
- "automatic song selection experiments" that contain the experiments related to the central part of the article, _i.e.,_ how to select pairs of songs that will be blended automatically. 

This repository is a regrouping of two other repositories:
- https://github.com/MichaelMikkles/AutoMashup/
- https://github.com/LeaMyl/Automashup_Mashup_Eval/

which were the practical repositories used for development.

## Examples

Below are two examples of Mashups obtained from the FMA music archive. As you will see, the mashups are still far from being of professional audio quality. Future work will be dedicated to enhancing the audio quality, and notably using automatic mixing tools like [DMC](https://csteinmetz1.github.io/dmc-icassp2021/).

### Original song A

https://github.com/user-attachments/assets/12994748-8c7e-48be-9450-7e86a9f23dec

### Original song B

https://github.com/user-attachments/assets/b050b29c-5a3d-4256-aa47-b8eba0612e1c

### Mashup: Vocal A + Instr B

https://github.com/user-attachments/assets/b3574d31-0a44-4c0a-bbdf-9b6fb796892a

### Mashup: Vocal B + Instr A

https://github.com/user-attachments/assets/0120a2b1-13a0-4517-a89e-8bd7325ea3a8

## Installation
So, many external packages essential for this project do not follow the recent releases. Hence, installation is becoming increasingly complex.

To ensure that there won't be a problem, you should definitely fix Python to 3.10, and follow these steps (I'm sorry for the inconvenience).

### Set up a virtualenv
First, set up the virtual environment. You may use the tool that you prefer, but we used conda on our side, hence we recommend it.

```bash
conda create -n venv_name python=3.10
conda activate venv_name
```

### Install the requirements
Now, you should install the required dependencies:

```bash
pip install -r requirements.txt
```

### Installing natten (for allin1)

This is one of the main problems. You should install natten so that it works with allin1. But allin1 was developed using old versions of natten, hence it is suited to work with precise versions.

So, you should use one precise version of natten, the following:

```bash
pip install natten==0.17.3+torch220cu121 -f https://shi-labs.com/natten/wheels
```

### Installing automashup

Finally, you can install the package automashup:
```bash
pip install -e /path/to/automashup/files (often, it is just ".")
```

### Installing rubberband-cli

The last mandatory step is to install rubberband-cli on your machine, using:

```bash
sudo apt-get install rubberband-cli
```

### (Optional) Install FFmpeg for MP3 support
Finally, for mp3 support, you have to install ffmpeg
```bash
sudo apt install ffmpeg
```


## GUI: Launch the barfi application
Automashup comes with a GUI that you may launch using the following steps:

> cd ./automashup/app

> streamlit run app.py

## Sandbox
Some tests were made using DMC for mixing, and should be pursued shortly. To install and test DMC on your own: https://github.com/csteinmetz1/automix-toolkit (clone + set up (modify sklearn --> scikit-learn in the setup.py) and test directly on your machine, don't forget to change the paths)

## Docker Image

We have a Docker image of the automashup app; it's only been tested on Linux :
https://hub.docker.com/r/gaubiche/automashup/

## Adding Mashup Methods

This interface aims to present multiple mashup techniques.

You can add some to the application by creating a mashup function in the file /src/mashup.py and then modifying the file src/app.py

If you want to experiment with new mashup methods, you can use the /automashup-notebook/notebook.ipynb file. It shows an example of a working mashup method.
