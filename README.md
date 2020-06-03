# TinyFPGA-Programmer-Application
Desktop application for programming TinyFPGA boards updated to pythoin3 and for QuickLogic's QuickFeather including CLI support

## How to checkout the git repo with the sub-modules
This git repo uses sub-modules to link to other git repos on github.  In order to clone the repo as well as the sub-modules you need to add an extra option to your clone command-line:

```sh
git clone --recursive https://github.com/QuickLogic-Corp/TinyFPGA-Programmer-Application.git
```

The `--recursive` argument tells git to clone all the sub-modules as well.  For more information on how git sub-modules work, check out this [Git Submodules basic explanation](https://gist.github.com/gitaarik/8735255).

Once you've cloned the repo you can launch the programmer with python:
```sh
cd TinyFPGA-Programmer-Application
python3 tinyfpga-programmer-gui.py
```
