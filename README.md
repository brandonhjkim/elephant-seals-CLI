# Seal Counter CLI - User Guide

Welcome to the **Seal Counter CLI**! This guide will walk you through the installation and usage of the command-line interface for counting seals in images.

This program is designed to help you count seals in images using a pre-trained model. It is built using Python and packaged for easy installation and usage.

## Prerequisites
Before you start, ensure you have:
- A computer with Windows, macOS, or Linux
- An internet connection
- **Python 3.8 - 3.12**

---

## Step 1: Install Python (Version 3.8 - 3.12)

If you don't have Python installed:

1. Visit the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download a version within **3.8 to 3.12** for your operating system (This program was built using **Python 3.10.4** so we recommend using that)
3. Run the installer and **check the box** that says `Add Python to PATH` before clicking `Install Now`.
4. Verify the installation:
   - Open a terminal (Command Prompt, PowerShell, or Terminal)
   - Type:
     ```sh
     python --version
     ```
   - You should see something like `Python 3.x.x` (where `x.x` is your version).

---

## Step 2: Install ESD CLI Package Using pip
1. Open a terminal (Command Prompt, PowerShell, or Terminal).
2. Install the package using pip:
    ```sh
    pip install https://github.com/brandonhjkim/elephant-seals-CLI/releases/download/1.1.0/elephant_seals_counter-1.1.0-py3-none-any.whl
    ```
3. Ensure you are downloading the latest version of the package from the [releases page](
    https://github.com/brandonhjkim/elephant-seals-CLI/releases).
3. Verify the installation:
    - Type:
      ```sh
      pip show elephant_seals_counter
      ```
    - You should see package information including the version.

---

## Step 3: Run the Seal Counter CLI

1. Once the virtual environment is set up, run the program using:
    ```sh
    seal-counter
    ```
2. Follow the on-screen instructions to provide a API key or accept the default one.
3. When the program runs, it will ask you to **provide a folder path** within the repository. Simply type the path and press `Enter` when prompted. 
There is currently an existing folder in this repository named "beach_images" with 2 beaches already uploaded as examples. 
To have this model run on new images, upload new beach images into that folder, type in "beach_images" when prompted for a folder, and be patient!
You can also upload a new folder of images that you can specify for this program to run with. Please make sure that new images are formatted in one of the following file extensions: `.jpeg` `.png` `.jpg` `.tif` `.tiff`

---

## Troubleshooting
- **Command not found?** Ensure Python is installed and added to PATH.

If you need further help, feel free to open an issue on this repository!

---

## Additional Info
Please do not change the assets folder or the .gitignore file! They are essential to making sure this repository functions and updates properly! 

Enjoy using **Seal Counter CLI**!

## Web App

Make sure to check out [this repository](https://github.com/ishaansathaye/elephant-seals-detection?tab=readme-ov-file) for the web app interface!

