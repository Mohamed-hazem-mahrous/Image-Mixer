from PyQt5.QtWidgets import QWidget, QFileDialog
from vp import Ui_Viewport
import pyqtgraph as pg
import numpy as np
import cv2
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QSlider
from PyQt5.QtCore import Qt, QRectF, QObject, QPointF, QMetaProperty, pyqtSignal
from PyQt5.QtWidgets import QMenu, QAction
import logging

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

class SignalEmitter(QObject):
    sig_ROI_changed = pyqtSignal(pg.ROI)
    objectCreated = pyqtSignal()

class Viewport(QtWidgets.QWidget, Ui_Viewport):
    def __init__(self, parent: QWidget | None):
        super(Viewport, self).__init__(parent)
        self.setupUi(self)
        
        # Flags to allow altering the widget's funcionality
        self.ft_enabled = True
        self.can_browse = True
        
        # Signal emiiter class to emit custom signals
        self.sig_emitter = SignalEmitter()
        
        

        self.ROI_Maxbounds = QRectF(0, 0, 100, 100)

        self.brightness_val = 1
        self.contrast_val = 1



        self.img_data = None

        self.img_data_dict = {
            IMG_IN: None,
            IMG_OUT: None,
            RAW_IMG: None,
            DATA_IMG_ORIG: None,
            DATA_IMG: None,
            DATA_IMG_FT: None,
            DATA_IMG_FT_SHIFTED: None,
            FT_MAG: None,
            FT_PHASE: None,
            FT_REAL: None,
            FT_IMAG: None
        }

        self.img_data_modified_dict = {
            IMG_IN: None,
            IMG_OUT: None,
            RAW_IMG: None,
            DATA_IMG_ORIG: None,
            DATA_IMG: None,
            DATA_IMG_FT: None,
            DATA_IMG_FT_SHIFTED: None,
            FT_MAG: None,
            FT_PHASE: None,
            FT_REAL: None,
            FT_IMAG: None
        }

        self.initial_roi_position = None


        self.cmbx_ft.currentIndexChanged.connect(lambda :self.plot_ft_data(self.cmbx_ft.currentText()))
        
        self.image_view = self.plot_img.addViewBox()
        self.image_view.setAspectLocked(True)
        self.image_view.setMouseEnabled(x=False, y=False)
        self.image_view.setMenuEnabled(False)
            
        self.ft_view = self.plot_ft.addViewBox()
        self.ft_view.setAspectLocked(True)
        self.ft_view.setMouseEnabled(x=False, y=False)
        self.ft_view.setMenuEnabled(False)

        
        self.img_item = pg.ImageItem()
        self.img_item_ft = pg.ImageItem()
        self.image_view.addItem(self.img_item)
        self.ft_view.addItem(self.img_item_ft)

        

        
        # Creating ROI
        self.ft_roi = pg.ROI(pos = self.ft_view.viewRect().center(), size = (50, 50), hoverPen='b', resizable= True, invertible= True, rotatable= False, maxBounds= self.ROI_Maxbounds)
        self.ft_view.addItem(self.ft_roi)
        self.add_scale_handles_ROI(self.ft_roi)      
        

        
        # Connecting ROI signal to update region of data selected
        self.ft_roi.sigRegionChangeFinished.connect(lambda: self.region_update(finish = True))
        
        # Connect doubleClicked signal to the custom slot
        self.plot_img.scene().sigMouseClicked.connect(self.open_Img_file)


        self.plot_img.scene().sigMouseClicked.connect(lambda event: self.reset_brightness_contrast() if event.button() == 2 else None)
        self.plot_ft.scene().sigMouseClicked.connect(lambda event: self.reset_ROI() if event.button() == 2 else None)



        # Override the mouseMoveEvent method to prevent default behavior
        self.img_item.mouseDragEvent = self.mouse_drag_bright_change
        
        
        # Load default image
        # img_path = 'Boxx.png'
        # self.load_image(img_path)
        
    
    def region_update(self, finish=False):
        if finish:
            self.sig_emitter.sig_ROI_changed.emit(self.ft_roi)
        self.img_data_modified_dict[IMG_OUT], self.img_data_modified_dict[IMG_IN] =  np.fft.ifft2(np.fft.ifftshift(self.return_region_slice()))
        logging.debug('Region update finished')

    def return_region_slice(self):
        data = self.img_data_dict[DATA_IMG_FT_SHIFTED]
        data_slice_indices, QTrans = self.ft_roi.getArraySlice(data, self.img_item_ft, returnSlice=True)
        
        mask = np.full(data.shape, False)
        mask[data_slice_indices] = True
        masked_data_in = data * mask
        masked_data_out = data.copy()
        masked_data_out[mask] = 0
        logging.debug('Region slice returned')
        return (masked_data_in, masked_data_out)

    def open_Img_file(self, event):
        if self.can_browse:
            if event.double():
                file_dialog = QFileDialog(self)
                file_dialog.setNameFilter("Images (*.png *.jpg *.bmp *.tif)")
                file_dialog.setWindowTitle("Open Image File")
                file_dialog.setFileMode(QFileDialog.ExistingFile)
                if file_dialog.exec_() == QFileDialog.Accepted:
                    selected_file = file_dialog.selectedFiles()[0]
                    self.load_image(selected_file)
                    logging.info(f'Loaded image: {selected_file}')

    def load_image(self, img_path):
        self.img_data_dict[RAW_IMG] = cv2.imread(img_path)
        self.img_data = cv2.rotate(cv2.cvtColor(cv2.imread(img_path), cv2.COLOR_BGR2GRAY), cv2.ROTATE_90_CLOCKWISE)
        self.img_data_dict[DATA_IMG] = self.img_data
        self.img_data_dict[DATA_IMG_ORIG] = self.img_data
        self.img_data_modified_dict[DATA_IMG] = self.img_data
        self.calc_imag_ft(self.img_data_dict)
        self.calc_imag_ft(self.img_data_modified_dict)
        self.display_img(self.img_data_dict[DATA_IMG])
        self.ROI_Maxbounds.adjust(0, 0, self.img_item_ft.width(), self.img_item_ft.height())
        self.reset_ROI()
        logging.debug('Loaded image: {img_path}')

    def calc_imag_ft(self, Dict):
        mode = self.cmbx_ft.currentText()
        if Dict[DATA_IMG] is None or Dict[DATA_IMG].size == 0:
            return
        Dict[DATA_IMG_FT] = np.fft.fft2(Dict[DATA_IMG])
        Dict[DATA_IMG_FT_SHIFTED] = np.fft.fftshift(Dict[DATA_IMG_FT])
        Dict[FT_MAG] = np.abs(Dict[DATA_IMG_FT_SHIFTED])
        Dict[FT_PHASE] = np.angle(Dict[DATA_IMG_FT_SHIFTED])
        Dict[FT_REAL] = np.real(Dict[DATA_IMG_FT_SHIFTED])
        Dict[FT_IMAG] = np.imag(Dict[DATA_IMG_FT_SHIFTED])
        self.plot_ft_data(mode)
        logging.debug('Calculated Fourier transform')

    def plot_ft_data(self, mode):
        if mode == FT_PHASE:
            self.img_item_ft.setImage(self.img_data_dict[mode])
        else:
            self.img_item_ft.setImage(np.log(1 + self.img_data_dict[mode]))
        logging.debug(f'Plotted Fourier transform data: {mode}')

    def display_img(self, data):
        self.img_item.setImage(data)
        logging.debug('Displayed image')

    def update_brightness_contrast(self):
        adjusted_image = cv2.convertScaleAbs(self.img_data_dict[DATA_IMG_ORIG], alpha=1 + (self.contrast_val / 100.0),
                                             beta=self.brightness_val)
        self.img_data_dict[DATA_IMG] = adjusted_image
        self.img_data_modified_dict[DATA_IMG] = adjusted_image
        if self.ft_enabled:
            self.region_update(finish=True)
        self.calc_imag_ft(self.img_data_dict)
        self.calc_imag_ft(self.img_data_modified_dict)
        self.display_img(adjusted_image)
        logging.debug('Updated brightness and contrast')

    def mouse_drag_bright_change(self, event):
        drag_distance = event.pos() - event.lastPos()
        brightness_delta = drag_distance.x() * 3
        contrast_delta = drag_distance.y() * 3
        self.brightness_val = max(0, min(100, self.brightness_val + brightness_delta))
        self.contrast_val = max(0, min(100, self.contrast_val + contrast_delta))
        self.update_brightness_contrast()
        logging.debug('Mouse drag changed brightness and contrast')

    def reset_brightness_contrast(self):
        self.img_data_dict[DATA_IMG] = self.img_data_dict[DATA_IMG_ORIG]
        self.img_data_modified_dict[DATA_IMG] = self.img_data_dict[DATA_IMG_ORIG]
        if self.ft_enabled:
            self.region_update(finish=True)
        self.calc_imag_ft(self.img_data_dict)
        self.calc_imag_ft(self.img_data_modified_dict)
        self.display_img(self.img_data_dict[DATA_IMG_ORIG])
        logging.debug('Reset brightness and contrast')

    

    
##===============================## Helper Functions ##===============================##
    
    def add_scale_handles_ROI(self, roi : pg.ROI):
        positions = np.array([[0,0], [1,0], [1,1], [0,1]])
        for pos in positions:        
            roi.addScaleHandle(pos = pos, center = 1 - pos)
            
    
    def center_ROI_to_image(self):
        roi_rect = self.ft_roi.size()
        half_width = roi_rect[0] / 2
        half_height = roi_rect[1] / 2
        center = self.img_item_ft.boundingRect().center()
        adjusted_center = [center.x() - half_width, center.y()- half_height]
        self.ft_roi.setPos(adjusted_center)
        logging.debug('ROI centered to image')
        
        
    def set_ROI_size_to_image(self):
        self.ft_roi.setSize(size=(self.img_item_ft.boundingRect().width(), self.img_item_ft.boundingRect().height()))
        logging.debug('ROI size set to image size')
        
        
    def reset_ROI(self):
        self.set_ROI_size_to_image()
        self.center_ROI_to_image()
        logging.debug('Reset ROI')
        
    def set_properties(self):
        self.ft_enabled = self.property('ft_enabled')
        self.can_browse = self.property('can_browse')
        self.wgt_ft.setVisible(self.ft_enabled)
        logging.debug(f'Properties set: ft_enabled={self.ft_enabled}, can_browse={self.can_browse}')

           




if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    window = Viewport(None)
    window.show()
    app.exec_()
