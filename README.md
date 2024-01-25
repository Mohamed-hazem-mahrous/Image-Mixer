# Mixer Application


## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Video Demonstration](#Video-Demonstration)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)



## Introduction
This repository contains the source code for a PyQt-based mixer application designed for image processing. The application allows users to load multiple images, apply various operations on them, and visualize the results. 


## Features

- **Image Loading**: Users can open image files (PNG, JPG, BMP, TIFF) using the file dialog. The loaded images are displayed in separate viewports.

- **Four Viewports**: The application provides four viewports, each displaying a different image. Users can resize and manipulate regions of interest (ROI) in one viewport, and the changes will be reflected in all viewports.

- **Image Processing**: The application supports various image processing operations, including Fourier Transform (FT) magnitude and phase visualization. Users can adjust weights for each image and choose the operation mode.

- **Output Display**: Processed images are displayed in two separate output viewports, allowing users to compare different results.

- **Brightness and Contrast Adjustment**: Users can adjust the brightness and contrast of the images interactively.


## Video Demonstration
[App Demo](https://github.com/Mohamed-hazem-mahrous/Image-Mixer/assets/94749599/1d0b9028-cf0c-4ad0-be3e-d2b652f871e1)



## Requirements
List the dependencies and requirements needed to run the application.
- PyQt5
- NumPy
- Open CV
- PyQtGraph


## Installation

Install the required dependencies using pip

```bash
pip install PyQt5 numpy opencv-python pyqtgraph
```

## Usage
Run the application:
```bash
python ImageMixer.py
```
### Loading Images

- Double-click on a viewport to open the file dialog and select an image file.
- Supported formats: PNG, JPG, BMP, TIFF.

### Adjusting ROI

- In each viewport, a region of interest (ROI) can be resized and manipulated.
- Changes in one viewport are synchronized with all viewports.

### Weighted Mixing

- Adjust the weights of each image using the sliders.
- Select the desired mode (e.g., FT Magnitude) from the dropdown menu.

### Displaying Output

- Click the "Mix" button to apply the weights and display the processed image.
- Choose the output viewport using radio buttons.

### Brightness and Contrast Adjustment

- Interactively adjust brightness and contrast using mouse drag in the image view.

## Contributing
Contributions to Signal Viewer are welcome! If you encounter any issues or have suggestions for improvements, please create a new issue or submit a pull request.

When contributing, please ensure that you follow the existing coding style and include clear commit messages to maintain a well-documented project history.

