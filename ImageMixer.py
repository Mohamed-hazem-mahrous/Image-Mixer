import sys
import typing
import cv2
from PyQt5.QtWidgets import QWidget, QMessageBox
from mainUi import Ui_MainWindow
from PyQt5 import QtCore, QtWidgets, uic
from pyqtgraph import ViewBox
import pyqtgraph as pg
import numpy as np
import logging
import threading
import time


logging.basicConfig(filename = 'application.log', level = logging.DEBUG, format = '%(asctime)s - %(levelname)s - %(message)s', filemode='w')


IMG_IN = "Img In"
IMG_OUT = "Img Out"
RAW_IMG = "Raw Img"
DATA_IMG_ORIG = "Img Data Orig"
DATA_IMG = "Img Data"
DATA_IMG_FT = "Img Data FT"
DATA_IMG_FT_SHIFTED = "Img Data FT Shifted"
FT_MAG = "FT Magnitude"
FT_PHASE = "FT Phase"
FT_REAL = "FT Real"
FT_IMAG = "FT Imaginary"



class MixerWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super(MixerWindow, self).__init__()
        self.setupUi(self)

        self.mean_val = 0
        self.invert_ROI = False # Controls whether to pick the data inside the ROI (False) or Outside it (True)

        # Used to get the custom properties set from Qt Designer
        self.viewport5.set_properties()
        self.viewport6.set_properties()

        # Output views' view boxes. Use these plus addItem() to add your image
        self.output_1 = self.viewport5
        self.output_2 = self.viewport6.image_view

        self.viewports = [self.viewport1, self.viewport2, self.viewport3, self.viewport4]
        self.sliders_weights = [self.slider_mix_1, self.slider_mix_2, self.slider_mix_3, self.slider_mix_4]
        self.sliders_labels = [self.lbl_image1, self.lbl_image2, self.lbl_image3, self.lbl_image4]

        self.weights = [1, 1, 1, 1]            
            
        self.other_mode = {
            FT_MAG: FT_PHASE,
            FT_REAL: FT_IMAG,
            FT_PHASE: FT_MAG,
            FT_IMAG: FT_REAL
        }

        for slider in self.sliders_weights:
            slider.valueChanged.connect(self.update_sliders_weights)
            slider.sliderReleased.connect(self.display_output)

        for view in self.viewports:
            view.plot_img.scene().sigMouseClicked.connect(self.resize_images)
            view.sig_emitter.sig_ROI_changed.connect(lambda roi: self.modify_all_regions(roi))

        
        self.chkbx_invert.stateChanged.connect(self.set_mask_state) 
        self.btn_mix.clicked.connect(self.display_output)


    # Sets the invert_ROI flag based on 'Invert Selection' checkbox state
    def set_mask_state(self):
        self.invert_ROI = self.chkbx_invert.isChecked()
        logging.debug(f'Invert ROI state set to: {self.invert_ROI}')

    def modify_all_regions(self, roi: pg.ROI):
        new_state = roi.getState()
        for view in self.viewports:
            if view.ft_roi is not roi:
                view.ft_roi.setState(new_state, update=False)
                view.ft_roi.stateChanged(finish=False)
                view.region_update(finish=False)
        logging.debug('All regions modified')

    def update_sliders_weights(self):
        for i in range(4):
            self.weights[i] = self.sliders_weights[i].value() / 10
            self.sliders_labels[i].setText(f"Image{i+1}:{int(self.weights[i] * 100)}%")
        logging.debug(f'Sliders weights updated: {self.weights}')

    def display_output(self):
        mode = self.cmbx_mix.currentText()
        modified_data = self.apply_weights(mode)

        if mode != FT_PHASE:
            modified_data = np.log(modified_data + 1)

        if self.radio_out_1.isChecked():
            self.display_view_out(self.viewport5, modified_data)
        elif self.radio_out_2.isChecked():
            self.display_view_out(self.viewport6, modified_data)
        logging.info(f'Displayed output for mode: {mode}')

    def display_view_out(self, out, data):
        out.img_data_dict[DATA_IMG] = data
        out.img_data_dict[DATA_IMG_ORIG] = data
        out.calc_imag_ft(out.img_data_dict)
        out.display_img(out.img_data_dict[DATA_IMG])
        logging.debug(f'Displayed view output')

    def get_mean_val(self):
        self.mean_val = 0
        for i in self.weights:
            if i != 0:
                self.mean_val += 1
        logging.debug(f'Mean value calculated: {self.mean_val}')

    def apply_weights(self, out_mode):
        mode_dat = 0
        other_dat = 0

        self.get_mean_val()

        progress_bar = QtWidgets.QProgressBar(self)
        progress_bar.setGeometry(30, 40, 200, 25)
        progress_bar.setMaximum(100)
        self.statusBar().addWidget(progress_bar)

        for index, (port, weight) in enumerate(zip(self.viewports, self.weights)):
            
            if self.chkbx_invert.isChecked():
                port.img_data_modified_dict[DATA_IMG] = port.img_data_modified_dict[IMG_OUT]
                port.calc_imag_ft(port.img_data_modified_dict)
            else:
                port.img_data_modified_dict[DATA_IMG] = port.img_data_modified_dict[IMG_IN]
                port.calc_imag_ft(port.img_data_modified_dict)

            mode = port.cmbx_ft.currentText()
            other = self.other_mode[mode]

            if mode == out_mode or other == out_mode:
                pass
            else:
                progress_bar.deleteLater()
                QMessageBox.critical(self, 'Invalid Pairs', 'Choose valid pairs: Mag/Phase or Real/Imaginary', QMessageBox.Ok)
                return

            if mode == FT_PHASE or mode == FT_IMAG:
                mode, other = other, mode

            if weight == 0:
                other_weight = 0
            else:
                other_weight = 1

            mode_dat += port.img_data_modified_dict[mode] * (weight / self.mean_val)
            other_dat += port.img_data_modified_dict[other] * (other_weight / self.mean_val)

            progress_value = int((index + 1) / len(self.viewports) * 100)
            progress_bar.setValue(progress_value)
            QtWidgets.QApplication.processEvents()

        progress_bar.deleteLater()

        if mode == FT_MAG:
            output = np.clip(np.abs(np.fft.ifft2(mode_dat * np.exp(1j * other_dat))), 0, 255)
        else:
            output = np.clip(np.abs(np.fft.ifft2(mode_dat + (1j * other_dat))), 0, 255)

        logging.debug(f'Applied weights and calculated output for mode: {mode}')
        return output

    def resize_images(self):
        min_height, min_width = self.viewports[0].img_data_dict[RAW_IMG].shape[:2]
        for port in self.viewports[1:]:
            img = port.img_data_dict[RAW_IMG]
            height, width = img.shape[:2]
            min_height = min(min_height, height)
            min_width = min(min_width, width)

        for i in range(4):
            self.viewports[i].img_data_dict[RAW_IMG] = cv2.resize(
                self.viewports[i].img_data_dict[RAW_IMG], (min_width, min_height)
            )

            new_img = cv2.rotate(cv2.cvtColor(self.viewports[i].img_data_dict[RAW_IMG], cv2.COLOR_BGR2GRAY), cv2.ROTATE_90_CLOCKWISE)
            self.viewports[i].img_data_dict[DATA_IMG] = new_img
            self.viewports[i].img_data_dict[DATA_IMG_ORIG] = new_img

            self.viewports[i].img_data_modified_dict[DATA_IMG] = new_img
            self.viewports[i].img_data_modified_dict[DATA_IMG_ORIG] = new_img

            self.viewports[i].calc_imag_ft(self.viewports[i].img_data_dict)
            self.viewports[i].calc_imag_ft(self.viewports[i].img_data_modified_dict)

            self.viewports[i].display_img(self.viewports[i].img_data_dict[DATA_IMG_ORIG])
        logging.debug('Resized images')


app = QtWidgets.QApplication(sys.argv)

window = MixerWindow()

window.show()

app.exec()
