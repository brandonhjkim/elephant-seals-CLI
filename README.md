# Seal Counter CLI - User Guide

Welcome to the **Seal Counter CLI**! This guide will walk you through the installation and usage of the command-line interface for counting seals in images.
This program is designed to help you count seals in images using a pre-trained model. It is built using Python and requires Docker for easy deployment.

## Prerequisites
Before you start, ensure you have:
- A computer with Windows, macOS, or Linux
- An internet connection
- **Docker**

---

## Step 1: Install Docker
If you don't have Docker installed:
1. Visit the official Docker website: [https://www.docker.com/get-started](https://www.docker.com/get-started)
2. Download and install Docker Desktop for your operating system.
3. Follow the installation instructions on the Docker website.
4. After installation, open Docker Desktop and ensure it is running.
5. Verify the installation:
   - Open a terminal (Command Prompt, PowerShell, or Terminal)
   - Type:
     ```sh
     docker --version
     ```
   - You should see something like `Docker version x.x.x` (where `x.x.x` is your version).

## Step 2: Build the Docker Image
1. Open a terminal and navigate to the project folder (where `Containerfile` is located):
   ```sh
   cd path/to/this/repository
   ```
2. Build the Docker image:
    ```sh
    docker build -t esd-cli .
    ```
3. Verify the image is built:
    - Type:
      ```sh
      docker images
      ```
    - You should see an image named `esd-cli` in the list.

## Step 3: Run the Docker Container
1. Run the Docker container:
   ```sh
   docker run -it --rm -v $(pwd):/app/data esd-cli
   ```
   - This command mounts the current directory to `/app/data` in the container.
2. The program will start running, and you will be prompted to provide a folder path.
    - Putting `.` will run the program on the current directory.
    - The program will also list subfolders in the current directory.
    - If running in the repository, you can use the `beach_images` folder as an example.
3. Follow the prompt to enter the folder path where your images are located.
4. The program will process the images and output the results.
5. Entering `exit` will stop the container and remove it.
6. To run the program again, simply repeat Step 3.

<!-- ## Step 1: Install Python (Version 3.8 - 3.12)

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

## Step 2: Create a Virtual Environment

1. Open a terminal and navigate to the project folder (where `seals_counter_cli.py` is located):
   ```sh
   cd path/to/this/repository
   ```
2. Create a virtual environment:
   ```sh
   python -m venv .venv
   ```
3. Install the required dependencies:
   ```sh
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## Step 3: Run the Seal Counter CLI

Once the virtual environment is set up, run the program using:
```sh
python seals_counter_cli.py
```
If you're returning to this program, and you've already set up the virtual environment on your computer (Step 2.), you need to run:
```sh
.venv\Scripts\activate
```
to reactive the virtual environment before running the program again. 

---

## Step 4: Follow the Prompt

When the program runs, it will ask you to **provide a folder path** within the repository. Simply type the path and press `Enter` when prompted. 
There is currently an existing folder in this repository named "beach_images" with 2 beaches already uploaded as examples. 
To have this model run on new images, upload new beach images into that folder, type in "beach_images" when prompted for a folder, and be patient!

You can also upload a new folder of images that you can specify for this program to run with. 

Please make sure that new images are formatted in one of the following file extensions: `.jpeg` `.png` `.jpg` `.tif` `.tiff`

--- -->

## Troubleshooting
<!-- - **Command not found?** Ensure Python is installed and added to PATH.
- **Virtual environment not activating?** Make sure you’re using the correct activation command for your system.
- **Missing dependencies?** Run `pip install -r requirements.txt` again. -->

If you need further help, feel free to open an issue on this repository!

---

## Additional Info
Please do not change the assets folder or the .gitignore file! They are essential to making sure this repository functions and updates properly! 

Enjoy using **Seal Counter CLI**!

## Web App

Make sure to check out [this repository](https://github.com/ishaansathaye/elephant-seals-detection?tab=readme-ov-file) for the web app interface!

