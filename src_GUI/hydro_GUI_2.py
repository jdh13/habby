import os
import numpy as np
import sys
from io import StringIO
from PyQt5.QtCore import QTranslator, pyqtSignal, QThread
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QGridLayout, QAction, qApp, \
    QTabWidget, QLineEdit, QTextEdit, QFileDialog, QSpacerItem, QListWidget,  QListWidgetItem, QComboBox, QMessageBox,\
    QStackedWidget, QRadioButton, QCheckBox
import h5py
import time
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import threading
from src import Hec_ras06
from src import hec_ras2D
from src import selafin_habby1
from src import substrate
from src import rubar
from src import river2d
from src import mascaret
from src import manage_grid_8
from src import dist_vistess2
np.set_printoptions(threshold=np.inf)

class Hydro2W(QWidget):
    """
    A class to load the hydrological data
    List of model supported:
    - TELEMAC
    - HEC-RAS
    - RUBAR
    - MASCARET
    - RIVER2D
    """
    def __init__(self, path_prj, name_prj):

        super().__init__()
        self.mod = QComboBox()
        #self.mod_loaded = QComboBox()
        self.path_prj = path_prj
        self.name_prj = name_prj
        self.name_model = ["", "HEC-RAS 1D", "HEC-RAS 2D", "MASCARET", "RIVER2D", "RUBAR BE", "RUBAR 20", "TELEMAC"]  # "MAGE"
        self.mod_act = 0
        self.stack = QStackedWidget()
        self.msgi = QMessageBox()
        self.init_iu()

    def init_iu(self):
        # generic label
        #self.l1 = QLabel(self.tr('blob'))
        l2 = QLabel(self.tr('<b> LOAD NEW DATA </b>'))
        l3 = QLabel(self.tr('<b>Available hydrological models </b>'))

        # available model
        #self.mod_loaded.addItems([""])
        self.mod.addItems(self.name_model)
        self.mod.currentIndexChanged.connect(self.selectionchange)
        self.button1 = QPushButton(self.tr('Model Info'), self)
        self.button1.clicked.connect(self.give_info_model)
        spacer2 = QSpacerItem(50, 1)
        spacer = QSpacerItem(1, 50)

        # add the widgets representing the available models to a stack of widget
        self.free = FreeSpace()
        self.hecras1D = HEC_RAS1D(self.path_prj, self.name_prj)
        self.hecras2D = HEC_RAS2D(self.path_prj, self.name_prj)
        self.telemac = TELEMAC(self.path_prj, self.name_prj)
        self.rubar2d = Rubar2D(self.path_prj, self.name_prj)
        self.rubar1d = Rubar1D(self.path_prj, self.name_prj)
        self.mascar = Mascaret(self.path_prj, self.name_prj)
        self.riverhere2d = River2D(self.path_prj, self.name_prj)
        self.stack.addWidget(self.free)  # order matters in the next lines!
        self.stack.addWidget(self.hecras1D)
        self.stack.addWidget(self.hecras2D)
        self.stack.addWidget(self.mascar)
        self.stack.addWidget(self.riverhere2d)
        self.stack.addWidget(self.rubar1d)
        self.stack.addWidget(self.rubar2d)
        self.stack.addWidget(self.telemac)
        self.stack.setCurrentIndex(self.mod_act)

        # layout
        self.layout4 = QGridLayout()
        self.layout4.addWidget(l3, 0, 0)
        self.layout4.addWidget(self.mod, 1, 0)
        self.layout4.addItem(spacer2, 1, 1)
        self.layout4.addWidget(self.button1, 1, 2)
        self.layout4.addWidget(self.stack, 2, 0)
        #self.layout4.addWidget(self.l1, 3, 0)
        #self.layout4.addWidget(self.mod_loaded, 4, 0)
        self.layout4.addItem(spacer, 3, 1)
        self.setLayout(self.layout4)

    def selectionchange(self, i):
        """
        Change the widget reprsenting each hydrological model (all widget are in a stack)
        :param i: the number of the model (0=no model, 1=hecras1d, 2= hecras2D,...)
        :return:
        """

        self.mod_act = i
        self.stack.setCurrentIndex(self.mod_act)

    def give_info_model(self):
        """
        A function to show extra information about each hydrological model.
        The information should be in a text file with the same as the model in the model_hydo folder
        General info goes as the startof the text file. If the text is too long, add the keyword "MORE INFO"
        and the message box will add the supplementary information
        :return: None
        """

        self.msgi.setIcon(QMessageBox.Information)
        text_title = self.tr("Information on ")
        mod_name = self.name_model[self.mod_act]
        self.msgi.setWindowTitle(text_title + mod_name)
        info_filename = os.path.join('./model_hydro', mod_name+'.txt')
        self.msgi.setStandardButtons(QMessageBox.Ok)
        if os.path.isfile(info_filename):
            with open(info_filename, 'rt') as f:
                text = f.read()
            text2 = text.split('MORE INFO')
            self.msgi.setText(text2[0])
            self.msgi.setDetailedText(text2[1])
        else:
            self.msgi.setText(self.tr('No information yet!         '))
            self.msgi.setDetailedText('No detailed info yet.')
        self.msgi.setEscapeButton(QMessageBox.Ok)  # detailed text erase the red x
        self.msgi.show()


class FreeSpace(QWidget):
    """
    Very simple class with empty space, just to have only Qwidget in the stack
    """
    def __init__(self):

        super().__init__()
        self.spacer = QSpacerItem(1, 1)
        self.layout_s = QGridLayout()
        self.layout_s.addItem(self.spacer, 0, 0)
        self.setLayout(self.layout_s)


class SubHydroW(QWidget):
    """
    a class which is the parent of the class which can be used to open the hydrological model.
    So there are MainWindiws which provides the windows around the widget,
    Hydro2W which provide the widget in the windows and one class by hydrological model to really load the model.
    The latter classes have various methods in common, so they inherit from SubHydroW, this class.
    """

    send_log = pyqtSignal(str, name='send_log')

    def __init__(self, path_prj, name_prj):

        self.namefile = ['unknown file', 'unknown file']  # for children, careful with list index out of range
        self.interpo = ["Interpolation by block", "Linear interpolation", "Nearest Neighbors"]  # order matters here
        self.interpo_choice = 0 # gives which type of interpolation is chosen (it is the index of self.interpo )
        self.pathfile = ['.', '.']
        self.attributexml = [' ', ' ']
        self.model_type = ' '
        self.nb_dim = 2
        self.save_fig = False
        self.coord_pro = []
        self.vh_pro = []
        self.nb_pro_reach = []
        self.on_profile = []
        self.xhzv_data = []
        self.inter_vel_all_t = []
        self.inter_h_all_t = []
        self.ikle_all_t = []
        self.point_all_t = []
        self.point_c_all_t = []
        self.np_point_vel = -99  # -99 -> velocity calculated in the same point than the profile height
        self.manning1 =0.025
        self.pro_add = 2  # additional profil during the grid creation
        self.extension = [[".txt"]]
        self.path_prj = path_prj
        self.name_prj = name_prj
        self.msg2 = QMessageBox()
        self.mystdout = None
        super().__init__()

    def was_model_loaded_before(self, i=0, many_file=False):
        """
        A function to test if the model loaded before, if yes, update the attibutes anf the widgets
        :param i a number in case there is more than one file to load
        :param many_file if true it will load more than one file, separated by ','
        :return:
        """
        filename_path_pro = os.path.join(self.path_prj, self.name_prj + '.xml')
        if os.path.isfile(filename_path_pro):
            doc = ET.parse(filename_path_pro)
            root = doc.getroot()
            child = root.find(".//" + self.attributexml[i])
            # if there is data in the project file about the model
            if child is not None:
                geo_name_path = child.text
                if os.path.isfile(geo_name_path) and not many_file:
                    self.namefile[i] = os.path.basename(geo_name_path)
                    self.pathfile[i] = os.path.dirname(geo_name_path)
                # load many file at once
                elif many_file:
                    list_all_name = geo_name_path.split(',\n')
                    for j in range(0, len(list_all_name)):
                        if os.path.isfile(list_all_name[j]):
                            self.namefile.append(os.path.basename(list_all_name[j]))
                            self.pathfile.append(os.path.dirname(list_all_name[j]))
                        else:
                            self.msg2.setIcon(QMessageBox.Warning)
                            self.msg2.setWindowTitle(self.tr("Previously Loaded File"))
                            self.msg2.setText(self.tr("One of the file given in the project file does not exist." ))
                            self.msg2.setStandardButtons(QMessageBox.Ok)
                            self.msg2.show()
                else:
                    self.msg2.setIcon(QMessageBox.Warning)
                    self.msg2.setWindowTitle(self.tr("Previously Loaded File"))
                    self.msg2.setText(
                        self.tr("The file given in the project file does not exist. Hydrological model:" + self.model_type))
                    self.msg2.setStandardButtons(QMessageBox.Ok)
                    self.msg2.show()

    def show_dialog(self, i=0):
        """
        A function to obtain the name of the file chosen by the user
        :param i a number in case there is more than one file to load
        :return: the name of the file, the path to this file
        """

        # find the filename based on user choice

        if len(self.pathfile) == 0:
            filename_path = QFileDialog.getOpenFileName(self, 'Open File', self.path_prj)[0]
        elif i >= len(self.pathfile):
            filename_path = QFileDialog.getOpenFileName(self, 'Open File', self.pathfile[0])[0]
        else:
            # why [0] : getOpenFilename return a tuple [0,1,2], we need only the filename
            filename_path = QFileDialog.getOpenFileName(self, 'Open File', self.pathfile[i])[0]
        # exeption: you should be able to clik on "cancel"
        if not filename_path:
            pass
        else:
            filename = os.path.basename(filename_path)
            # check extension
            extension_i = self.extension[i]
            blob, ext = os.path.splitext(filename)
            if any(e in ext for e in extension_i):
                pass
            else:
                self.msg2.setIcon(QMessageBox.Warning)
                self.msg2.setWindowTitle(self.tr("File type"))
                self.msg2.setText(self.tr("Needed type for the file to be loaded: " + ' ,'.join(extension_i)))
                self.msg2.setStandardButtons(QMessageBox.Ok)
                self.msg2.show()
            # keep the name in an attribute until we save it
            if i >= len(self.pathfile) or len(self.pathfile) == 0:
                self.pathfile.append(os.path.dirname(filename_path))
                self.namefile.append(filename)
            else:
                self.pathfile[i] = os.path.dirname(filename_path)
                self.namefile[i] = filename

    def save_xml(self, i=0, append_name = False):
        """
        A function to save the loaded data in the xml file
        :param i a number in case there is more than one file to save
        :param append_name. If True, name will be append to the existing namwe
        :return:
        """
        filename_path_file = os.path.join(self.pathfile[i], self.namefile[i])
        filename_path_pro = os.path.join(self.path_prj, self.name_prj + '.xml')
        # save the name and the path in the xml .prj file
        if not os.path.isfile(filename_path_pro):
            self.msg2.setIcon(QMessageBox.Warning)
            self.msg2.setWindowTitle(self.tr("Save Hydrological Data"))
            self.msg2.setText(
                self.tr("The project is not saved. Save the project in the General tab before saving data."))
            self.msg2.setStandardButtons(QMessageBox.Ok)
            self.msg2.show()
        else:
            doc = ET.parse(filename_path_pro)
            root = doc.getroot()
            # geo data
            child1 = root.find(".//"+self.model_type)
            if child1 is None:
                child1 = ET.SubElement(root, self.model_type)
            child = root.find(".//" + self.attributexml[i])
            if child is None:
                child = ET.SubElement(child1, self.attributexml[i])
                child.text = filename_path_file
            else:
                if append_name:
                    child.text += ",\n"
                    child.text += filename_path_file
                else:
                    child.text = filename_path_file
            doc.write(filename_path_pro, method="xml")

    def save_hdf5(self):
        """
        This function save the hydrological data in the hdf5 format.
        The log is not really finished, notbaly this functin cannot be used outise of the class,
        so it needs to be re-written if used in the command line
        :return:
        """
        self.send_log.emit('# Save hdf5 hydrological data')

        # create hdf5 name
        h5name = self.name_prj + '_' + self.model_type + '_' + time.strftime("%d_%m_%Y_at_%H_%M_%S") + '.h5'
        path_hdf5 = self.find_path_im()

        # create a new hdf5
        fname = os.path.join(path_hdf5, h5name)
        file = h5py.File(fname, 'w')

        # create attributes
        file.attrs['path_projet'] = self.path_prj
        file.attrs['name_projet'] = self.name_prj
        file.attrs['HDF5_version'] = h5py.version.hdf5_version
        file.attrs['h5py_version'] = h5py.version.version

        # create all datasets and group
        if self.nb_dim == 1:
            Data_1D = file.create_group('Data_1D')
            xhzv_datag = Data_1D.create_group('xhzv_data')
            xhzv_datag.create_dataset(h5name, data=self.xhzv_data)
        if self.nb_dim < 2:
            Data_15D = file.create_group('Data_15D')
            # is there a way to save inegal list in hdf5???
            # save nb_pro_reach somewhere
            for p in range(0, len(self.coord_pro)):
                coord_prog = Data_15D.create_group('coord_pro_profil_num_'+str(p))
                coord_prog.create_dataset(h5name, [4, len(self.coord_pro[p][0])], data=self.coord_pro[p])
            for t in range(0, len(self.vh_pro)):
                there = Data_15D.create_group('Timestep_' + str(t))
                for p in range(0, len(self.vh_pro[t])):
                    vh_prog = there.create_group('vh_pro_profil_num'+str(p))
                    vh_prog.create_dataset(h5name, [3, len(self.vh_pro[t][p][0])], data=self.vh_pro[t][p])
        if self.nb_dim <= 2:
            Data_2D = file.create_group('Data_2D')
            for t in range(0, len(self.ikle_all_t)):
                there = Data_2D.create_group('Timestep_'+str(t))
                for r in range(0, len(self.ikle_all_t[t])):
                    rhere = there.create_group('Reach_' + str(r))
                    ikleg = rhere.create_group('ikle')
                    ikleg.create_dataset(h5name, [len(self.ikle_all_t[t][r]), len(self.ikle_all_t[t][r][0])],
                                         data=self.ikle_all_t[t][r])
                    point_allg = rhere.create_group('point_all')
                    point_allg.create_dataset(h5name, [len(self.point_all_t[t][r]), 2], data=self.point_all_t[t][r])
                    point_cg = rhere.create_group('point_c_all')
                    point_cg.create_dataset(h5name, [len(self.point_c_all_t[t][r]), 2], data=self.point_c_all_t[t][r])
                    inter_velg = rhere.create_group('inter_vel_all')
                    inter_velg.create_dataset(h5name, [len(self.inter_vel_all_t[t][r])], data=self.inter_vel_all_t[t][r])
                    inter_hg = rhere.create_group('inter_h_all')
                    inter_hg.create_dataset(h5name, [len(self.inter_h_all_t[t][r])], data=self.inter_h_all_t[t][r])
        file.close()

        # save the file to the xml of the project
        filename_prj = os.path.join(self.path_prj, self.name_prj + '.xml')
        if not os.path.isfile(filename_prj):
            print('Error: No project saved. Please create a project first in the General tab.\n')
            return
        else:
            doc = ET.parse(filename_prj)
            root = doc.getroot()
            child = root.find(".//"+self.model_type)
            if child is None:
                stathab_element = ET.SubElement(root, self.model_type)
                hdf5file = ET.SubElement(stathab_element, "hdf5_hydrodata")
                hdf5file.text = fname
            else:
                hdf5file = root.find(".//"+self.model_type + "/hdf5_hydrodata")
                if hdf5file is None:
                    hdf5file = ET.SubElement(child, "hdf5_hydrodata")
                    hdf5file.text = fname
                else:
                    #hdf5file.text = hdf5file.text + ', ' + fname  # keep the name of the old and new file
                    hdf5file.text = fname   # keep only the new file
            doc.write(filename_prj)

        self.send_log.emit('restart SAVE_HYDRO_HDF5')
        self.send_log.emit('py    # save_hdf5 (function needs to be re-written to be used in cmd)')

        return

    def find_path_im(self):
        """
        A function to find the path where to save the figues, careful a simialr one is in estimhab_GUI.py
        :return: path_im
        """

        path_im = 'no_path'

        filename_path_pro = os.path.join(self.path_prj, self.name_prj + '.xml')
        if os.path.isfile(filename_path_pro):
            doc = ET.parse(filename_path_pro)
            root = doc.getroot()
            child = root.find(".//Path_Figure")
            if child is None:
                path_im = os.path.join(self.path_prj, 'figures_habby')
            else:
                path_im = child.text
        else:
            self.msg2.setIcon(QMessageBox.Warning)
            self.msg2.setWindowTitle(self.tr("Save Hydrological Data"))
            self.msg2.setText(
                self.tr("The project is not saved. Save the project in the General tab."))
            self.msg2.setStandardButtons(QMessageBox.Ok)
            self.msg2.show()


        return path_im

    def send_err_log(self):
        """
        Send the error and warning to the logs
        The stdout was redirected to self.mystdout
        :return:
        """
        str_found = self.mystdout.getvalue()
        str_found = str_found.split('\n')
        for i in range(0, len(str_found)):
            if len(str_found[i]) > 1:
                self.send_log.emit(str_found[i])

    def grid_and_interpo(self, cb_im):
        """
        this function form the link between GUI and the various grid and interpolation functions. Is called by
        the "loading' function of hec-ras 1D, Mascaret and Rubar BE.
        :param cb_im if true, the figures are created and shown.
        :return:
        """
        # preparation
        if not isinstance(self.interpo_choice, int):
            self.send_log.emit('Error: Interpolation method is not recognized (Type).\n')
            return
        if cb_im:
            path_im = self.find_path_im()
        if len(self.vh_pro) == 0:
            self.send_log.emit('Warning: Velocity and height data is empty (from grid_and_interpo)')
            return
        if len(self.vh_pro) == 1 and self.vh_pro == [-99]:
            self.send_log.emit('Error: Velocity and height data were not created.')
            return

        #all interpolations
        if self.interpo_choice == 0:
            self.send_log.emit(self.tr('# Create grid by block.'))
            for t in range(0, len(self.vh_pro)):
                sys.stdout = self.mystdout = StringIO()
                [ikle_all, point_all_reach, point_c_all, inter_vel_all, inter_height_all] = \
                    manage_grid_8.create_grid_only_1_profile(self.coord_pro, self.nb_pro_reach, self.vh_pro[t])
                if cb_im:
                    manage_grid_8.plot_grid(point_all_reach, ikle_all, [], [], [], point_c_all,
                                            inter_vel_all, inter_height_all, path_im)
                sys.stdout = sys.__stdout__
                self.send_err_log()
                self.inter_vel_all_t.append(inter_vel_all)
                self.inter_h_all_t.append(inter_height_all)
                self.ikle_all_t.append(ikle_all)
                self.point_all_t.append(point_all_reach)
                self.point_c_all_t.append(point_c_all)
                self.send_log.emit("py    vh_pro_t = vh_pro[" + str(t) + "]\n")
                self.send_log.emit("py    [ikle_all, point_all_reach, point_c_all, inter_vel_all, inter_height_all] = \
                    manage_grid_8.create_grid_only_1_profile(coord_pro, nb_pro_reach, vh_pro_t)\n")
                self.send_log.emit("restart INTERPOLATE_BLOCK")

        elif self.interpo_choice == 1:
            try:
                self.pro_add = int(self.nb_extrapro_text.text())
            except ValueError:
                self.send_log.emit('Error: Number of profile not recognized.\n')
                return
            self.send_log.emit(self.tr('# Create grid by linear interpolation.'))
            if not isinstance(self.pro_add, int):
                self.send_log.emit('Error: Number of profile not recognized.\n')
                return
            if 1 > self.pro_add > 500:
                self.send_log.emit('Error: Number of add. profiles should be between 1 and 500.\n')
                return
            for t in range(0, len(self.vh_pro)):
                # [], [] is used to add the substrate as a condition directly
                sys.stdout = self.mystdout = StringIO()
                [point_all_reach, ikle_all, lim_by_reach, hole_all, overlap, coord_pro2, point_c_all] = \
                    manage_grid_8.create_grid(self.coord_pro, self.pro_add,[], [], self.nb_pro_reach, self.vh_pro[t])
                sys.stdout = sys.__stdout__
                self.send_err_log()
                sys.stdout = self.mystdout = StringIO()
                [inter_vel_all, inter_height_all] = manage_grid_8.interpo_linear(point_c_all, coord_pro2, self.vh_pro[t])
                sys.stdout = sys.__stdout__
                self.send_err_log()
                self.inter_vel_all_t.append(inter_vel_all)
                self.inter_h_all_t.append(inter_height_all)
                self.ikle_all_t.append(ikle_all)
                self.point_all_t.append(point_all_reach)
                self.point_c_all_t.append(point_c_all)
                if cb_im:
                    manage_grid_8.plot_grid(point_all_reach, ikle_all, lim_by_reach,
                                            hole_all, overlap, point_c_all, inter_vel_all, inter_height_all, path_im)
                self.send_err_log()
                self.send_log.emit("py    vh_pro_t = vh_pro[" + str(t) + "]\n")
                self.send_log.emit("py    [point_all_reach, ikle_all, lim_by_reach, hole_all, overlap, coord_pro2,"
                                   " point_c_all] = manage_grid_8.create_grid(coord_pro, nb_pro_reach, vh_pro_t)\n")
                self.send_log.emit("py    [inter_vel_all, inter_height_all] = "
                                   "manage_grid_8.interpo_linear(point_c_all, coord_pro2, vh_pro_t))\n")
                self.send_log.emit("restart INTERPOLATE_LINEAR")

        elif self.interpo_choice == 2:
            try:
                self.pro_add = int(self.nb_extrapro_text.text())
            except ValueError:
                self.send_log.emit('Error: Number of profile not recognized.\n')
                return
            self.send_log.emit(self.tr('# Create grid by nearest neighbors interpolation.'))
            if 1 > self.pro_add > 500:
                self.send_log.emit('Error: Number of add. profiles should be between 1 and 500.\n')
                return
            for t in range(0, len(self.vh_pro)):
                sys.stdout = self.mystdout = StringIO()
                [point_all_reach, ikle_all, lim_by_reach, hole_all, overlap, coord_pro2, point_c_all] = \
                    manage_grid_8.create_grid(self.coord_pro, self.pro_add, [], [], self.nb_pro_reach, self.vh_pro[t])
                sys.stdout = sys.__stdout__
                self.send_err_log()
                sys.stdout = self.mystdout = StringIO()
                [inter_vel_all, inter_height_all] = manage_grid_8.interpo_nearest(self.point_c_all, coord_pro2, self.vh_pro[t])
                if cb_im:
                    manage_grid_8.plot_grid(point_all_reach, ikle_all, lim_by_reach,
                                            hole_all, overlap, point_c_all, inter_vel_all, inter_height_all, path_im)
                sys.stdout = sys.__stdout__
                self.send_err_log()
                self.inter_vel_all_t.append(inter_vel_all)
                self.inter_h_all_t.append(inter_height_all)
                self.ikle_all_t.append(ikle_all)
                self.point_all_t.append(point_all_reach)
                self.point_c_all_t.append(point_c_all)
                self.send_log.emit("py    vh_pro_t = vh_pro[" + str(t) + "]\n")
                self.send_log.emit("py    [point_all_reach, ikle_all, lim_by_reach, hole_all, overlap, coord_pro2,"
                                   " point_c_all] = manage_grid_8.create_grid(coord_pro, nb_pro_reach, vh_pro_t)\n")
                self.send_log.emit("py    [inter_vel_all, inter_height_all] = "
                                   "manage_grid_8.interpo_nearest(point_c_all, coord_pro2, vh_pro_t))\n")
                self.send_log.emit("restart INTERPOLATE_NEAREST")
        else:
            self.send_log.emit('Error: Interpolation method is not recognized (Num).\n')
        return

    def distribute_velocity(self):
        """
        This function make the link between the GUI and the functions of dist_vitesse2. It is used by 1D model,
        notably rubar and masacret.
        :return:
        """
        self.send_log.emit("# Velocity distribution")
        sys.stdout = self.mystdout = StringIO()
        manning_array = dist_vistess2.get_manning(self.manning1, self.np_point_vel, len(self.coord_pro))
        self.vh_pro = dist_vistess2.dist_velocity_hecras(self.coord_pro, self.xhzv_data, manning_array,
                                                         self.np_point_vel, 1, self.on_profile)
        sys.stdout = sys.__stdout__
        self.send_err_log()
        self.send_log.emit("restart GET_MANNING")
        self.send_log.emit("restart DISTRIBUTE VELOCITY")
        self.send_log.emit("py    manning1 = " + str(self.manning1))
        self.send_log.emit("py    np_point_vel = " + str(self.np_point_vel))
        self.send_log.emit("py    manning_array = dist_vistess2.get_manning(manning1, np_point_vel, len(coord_pro))")
        self.send_log.emit("py    vh_pro = dist_vistess2.dist_velocity_hecras(coord_pro, xhzv_data, manning_array, "
                           "np_point_vel, 1, on_profile)")


class HEC_RAS1D(SubHydroW):
    """
    The sub-windows which help to open the Hec-RAS data. Call the Hec-RAS loader and save the name
     of the files to the project xml file.
    """
    show_fig = pyqtSignal()

    def __init__(self, path_prj, name_prj):
        super().__init__(path_prj, name_prj)
        self.inter = QComboBox()
        self.init_iu()

    def init_iu(self):

        # update attibute for hec-ras 1d
        self.attributexml = ['geodata', 'resdata']
        self.model_type = 'HECRAS1D'
        self.extension = [['.g01', '.g02', '.g03', '.g04','.g05 ', '.g06', '.g07', '.g08',
                            '.g09', '.g10', '.g11', '.G01', '.G02'], ['.xml', '.rep', '.sdf']]
        self.nb_dim = 1.5

        # if there is the project file with hecras geo info, update the label and attibutes
        self.was_model_loaded_before(0)
        self.was_model_loaded_before(1)

        # label with the file name
        self.geo_t2 = QLabel(self.namefile[0], self)
        self.out_t2 = QLabel(self.namefile[1], self)

        # geometry and output data
        l1 = QLabel(self.tr('<b> Geometry data </b>'))
        self.geo_b = QPushButton('Choose file (.g0x)', self)
        self.geo_b.clicked.connect(lambda: self.show_dialog(0))
        self.geo_b.clicked.connect(lambda: self.geo_t2.setText(self.namefile[0]))
        l2 = QLabel(self.tr('<b> Output data </b>'))
        self.out_b = QPushButton('Choose file \n (.xml, .sdf, or .res file)', self)
        self.out_b.clicked.connect(lambda: self.show_dialog(1))
        self.out_b.clicked.connect(lambda: self.out_t2.setText(self.namefile[1]))

        # # grid creation options
        l6 = QLabel(self.tr('<b>Grid creation </b>'))
        l3 = QLabel(self.tr('Velocity distribution'))
        l31 = QLabel(self.tr('Model 1.5D: No dist. needed'))
        l4 = QLabel(self.tr('Interpolation of the data'))
        l5 = QLabel(self.tr('Number of additional profiles'))
        self.inter.addItems(self.interpo)
        self.nb_extrapro_text = QLineEdit('1')

        # load button
        self.load_b = QPushButton('Load data and create hdf5', self)
        self.load_b.clicked.connect(self.load_hec_ras_gui)
        self.spacer1 = QSpacerItem(1, 20)
        self.spacer2 = QSpacerItem(1, 20)
        self.cb = QCheckBox(self.tr('Show figures'), self)

        # layout
        self.layout_hec = QGridLayout()
        self.layout_hec.addWidget(l1, 0, 0)
        self.layout_hec.addWidget(self.geo_t2,0, 1)
        self.layout_hec.addWidget(self.geo_b, 0, 2)
        self.layout_hec.addWidget(l2, 1, 0)
        self.layout_hec.addWidget(self.out_t2, 1, 1)
        self.layout_hec.addWidget(self.out_b, 1, 2)
        self.layout_hec.addItem(self.spacer1, 2, 1)
        self.layout_hec.addWidget(l6, 3, 0)
        self.layout_hec.addWidget(l3, 4, 1)
        self.layout_hec.addWidget(l31, 4, 2, 1, 2)
        self.layout_hec.addWidget(l4, 5, 1)
        self.layout_hec.addWidget(self.inter, 5, 2, 1, 2)
        self.layout_hec.addWidget(l5, 6, 1)
        self.layout_hec.addWidget(self.nb_extrapro_text, 6, 2, 1, 2)
        self.layout_hec.addItem(self.spacer2, 7, 1)
        self.layout_hec.addWidget(self.load_b, 8, 3)
        self.layout_hec.addWidget(self.cb, 8, 2)
        #self.layout_hec.addItem(spacer, 4, 1)
        self.setLayout(self.layout_hec)

    def load_hec_ras_gui(self):
        """
        A function to exectue the loading and saving the the HEC-ras file using Hec_ras.py
        :return:
        """
        # update the xml file of the project
        self.save_xml(0)
        self.save_xml(1)
        path_im = self.find_path_im()

        # load hec_ras data
        if self.cb.isChecked() and path_im != 'no_path':
            self.save_fig = True
        # redirect the out stream to my output
        sys.stdout = self.mystdout = StringIO()
        [self.coord_pro, self.vh_pro, self.nb_pro_reach] = Hec_ras06.open_hecras(self.namefile[0], self.namefile[1], self.pathfile[0],
                                               self.pathfile[1], path_im, self.save_fig)
        sys.stdout = sys.__stdout__
        # log info
        self.send_log.emit(self.tr('# Load: Hec-Ras 1D data.'))
        self.send_err_log()
        self.send_log.emit("py    file1='"+ self.namefile[0] + "'")
        self.send_log.emit("py    file2='" + self.namefile[1] + "'")
        self.send_log.emit("py    path1='" + self.pathfile[0] + "'")
        self.send_log.emit("py    path2='" + self.pathfile[1] + "'")
        self.send_log.emit("py    [coord_pro, vh_pro, nb_pro_reach] = Hec_ras06.open_hecras(file1, file2, path1, path2, '.', False)\n")
        self.send_log.emit("restart LOAD_HECRAS_1D")
        self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[0],self.namefile[0]))
        self.send_log.emit("restart    file2: " + os.path.join(self.pathfile[1],self.namefile[1]))

        # grid and interpolation
        self.interpo_choice = self.inter.currentIndex()
        self.grid_and_interpo(self.cb.isChecked())

        #save hdf5 data
        self.save_hdf5()
        # show figure
        if self.cb.isChecked():
            self.show_fig.emit()


class Rubar2D(SubHydroW):
    """
    The sub-windows which help to open the rubar data. Call the rubar loader and save the name
     of the files to the project xml file.
    """
    show_fig = pyqtSignal()

    def __init__(self, path_prj, name_prj):

        super().__init__(path_prj, name_prj)
        self.init_iu()

    def init_iu(self):

        # update attibute for rubar 2d
        self.attributexml = ['rubar_geodata', 'tpsdata']
        self.model_type = 'RUBAR2D'
        self.extension = [['.mai', '.dat'], ['.tps']]  # list of list in case there is more than one possible ext.
        self.nb_dim = 2

        # if there is the project file with rubar geo info, update the label and attibutes
        self.was_model_loaded_before(0)
        self.was_model_loaded_before(1)

        # label with the file name
        self.geo_t2 = QLabel(self.namefile[0], self)
        self.out_t2 = QLabel(self.namefile[1], self)

        # geometry and output data
        l1 = QLabel(self.tr('<b> Geometry data </b>'))
        self.geo_b = QPushButton('Choose file (.mai, .dat)', self)
        self.geo_b.clicked.connect(lambda: self.show_dialog(0))
        self.geo_b.clicked.connect(lambda: self.geo_t2.setText(self.namefile[0]))
        self.geo_b.clicked.connect(self.propose_next_file)
        l2 = QLabel(self.tr('<b> Output data </b>'))
        self.out_b = QPushButton('Choose file \n (.tps)', self)
        self.out_b.clicked.connect(lambda: self.show_dialog(1))
        self.out_b.clicked.connect(lambda: self.out_t2.setText(self.namefile[1]))

        # grid creation
        l2D1 = QLabel(self.tr('<b>Grid creation </b>'))
        l2D2 = QLabel(self.tr('2D MODEL - No new grid needed.'))

        # load button
        self.load_b = QPushButton('Load data and create hdf5', self)
        self.load_b.clicked.connect(self.load_rubar)
        self.spacer = QSpacerItem(1, 80)
        self.cb = QCheckBox(self.tr('Show figures'), self)

        # layout
        self.layout_hec = QGridLayout()
        self.layout_hec.addWidget(l1, 0, 0)
        self.layout_hec.addWidget(self.geo_t2,0, 1)
        self.layout_hec.addWidget(self.geo_b, 0, 2)
        self.layout_hec.addWidget(l2, 1, 0)
        self.layout_hec.addWidget(self.out_t2, 1, 1)
        self.layout_hec.addWidget(self.out_b, 1, 2)
        self.layout_hec.addWidget(l2D1, 2, 0)
        self.layout_hec.addWidget(l2D2, 2, 1, 1, 2)
        self.layout_hec.addWidget(self.load_b, 3, 2)
        self.layout_hec.addWidget(self.cb, 3, 1)
        self.layout_hec.addItem(self.spacer, 4, 1)
        self.setLayout(self.layout_hec)

    def load_rubar(self):
        """
        A function to execture the loading and saving the the rubar file using rubar.py.
        :return:
        """
        # update the xml file of the project
        self.save_xml(0)
        self.save_xml(1)
        path_im = self.find_path_im()
        if self.cb.isChecked() and path_im != 'no_path':
            self.save_fig = True
        # load rubar 2d data
        sys.stdout = self.mystdout = StringIO()
        [self.inter_vel_all_t, self.inter_h_all_t, self.point_all_t, self.point_c_all_t, self.ikle_all_t] \
            = rubar.load_rubar2d(self.namefile[0], self.namefile[1],  self.pathfile[0], self.pathfile[1],
                                 path_im, self.save_fig)
        sys.stdout = sys.__stdout__

        # log info
        self.send_log.emit(self.tr('# Load: Rubar 2D data.'))
        self.send_err_log()
        self.send_log.emit("py    file1='" + self.namefile[0] + "'")
        self.send_log.emit("py    file2='" + self.namefile[1] + "'")
        self.send_log.emit("py    path1='" + self.pathfile[0] + "'")
        self.send_log.emit("py    path2='" + self.pathfile[1] + "'")
        self.send_log.emit("py    [v, h, coord_p, coord_c, ikle] = rubar.load_rubar2d(file1,"
                           " file2, path1, path2, '.', False)\n")
        self.send_log.emit("restart LOAD_RUBAR_2D")
        self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[0], self.namefile[0]))
        self.send_log.emit("restart    file2: " + os.path.join(self.pathfile[1], self.namefile[1]))

        # TEMPORARY correction because we have only one grid for all time step
        self.point_all_t = [[self.point_all_t]]
        self.point_c_all_t = [[self.point_c_all_t]]
        self.ikle_all_t = [[self.ikle_all_t]]

        self.save_hdf5()

        if self.cb.isChecked():
            self.show_fig.emit()

    def propose_next_file(self):
        """
        A function which avoid to the user to search for both file to load.
        it tries to find the second file when the first one is selected
        :return:
        """
        if len(self.extension[1]) == 1:
            if self.out_t2.text() == 'unknown file':
                blob = self.namefile[0]
                self.out_t2.setText(blob[:-len(self.extension[0][0])] + self.extension[1][0])
                # keep the name in an attribute until we save it
                self.pathfile[1] = self.pathfile[0]
                self.namefile[1] = blob[:-len(self.extension[0][0])] + self.extension[1][0]


class Mascaret(SubHydroW):
    """
    The sub widows which call the function to load the mascaret data and save the name of the mascaret file to the
     project xml file.
    """
    show_fig = pyqtSignal()

    def __init__(self, path_prj, name_prj):
        super().__init__(path_prj, name_prj)
        self.inter = QComboBox()
        self.init_iu()

    def init_iu(self):

        # update attibute for mascaret
        self.attributexml = ['gen_data', 'geodata_mas', 'resdata_mas']
        self.namefile = ['unknown file', 'unknown file', 'unknown file']
        self.pathfile = ['.', '.', '.']
        self.model_type = 'mascaret'
        self.extension = [['.xcas'], ['.geo'], ['.opt', '.rub']]
        self.nb_dim = 1

        # if there is the project file with mascaret info, update the label and attibutes
        self.was_model_loaded_before(0)
        self.was_model_loaded_before(1)
        self.was_model_loaded_before(2)

        # label with the file name
        self.gen_t2 = QLabel(self.namefile[0], self)
        self.geo_t2 = QLabel(self.namefile[1], self)
        self.out_t2 = QLabel(self.namefile[2], self)

        # general, geometry and output data
        l0 = QLabel(self.tr('<b> General data </b>'))
        self.gen_b = QPushButton('Choose file (.xcas)', self)
        self.gen_b.clicked.connect(lambda: self.show_dialog(0))
        self.gen_b.clicked.connect(lambda: self.gen_t2.setText(self.namefile[0]))
        l1 = QLabel(self.tr('<b> Geometry data </b>'))
        self.geo_b = QPushButton('Choose file (.geo)', self)
        self.geo_b.clicked.connect(lambda: self.show_dialog(1))
        self.geo_b.clicked.connect(lambda: self.geo_t2.setText(self.namefile[1]))
        l2 = QLabel(self.tr('<b> Output data </b>'))
        self.out_b = QPushButton('Choose file \n (.opt, .rub)', self)
        self.out_b.clicked.connect(lambda: self.show_dialog(2))
        self.out_b.clicked.connect(lambda: self.out_t2.setText(self.namefile[2]))

        # grid creation options
        l6 = QLabel(self.tr('<b>Grid creation </b>'))
        l3 = QLabel(self.tr('Velocity distribution'))
        l32 = QLabel(self.tr("Based on Manning's formula"))
        l7 = QLabel(self.tr("Nb. of velocity points by profile"))
        l8 = QLabel(self.tr("Manning coefficient"))
        l4 = QLabel(self.tr('Interpolation of the data'))
        l5 = QLabel(self.tr('Nb. of additional profiles'))
        self.inter.addItems(self.interpo)
        self.nb_extrapro_text = QLineEdit('1')
        self.nb_vel_text = QLineEdit('70')
        self.manning_text = QLineEdit('0.025')

        # load button
        self.load_b = QPushButton('Load data and create hdf5', self)
        self.load_b.clicked.connect(self.load_mascaret_gui)
        #spacer = QSpacerItem(1, 20)
        self.cb = QCheckBox(self.tr('Show figures'), self)

        # layout
        self.layout = QGridLayout()
        self.layout.addWidget(l0, 0, 0)
        self.layout.addWidget(self.gen_t2, 0, 1)
        self.layout.addWidget(self.gen_b, 0, 2)
        self.layout.addWidget(l1, 1, 0)
        self.layout.addWidget(self.geo_t2, 1, 1)
        self.layout.addWidget(self.geo_b, 1, 2)
        self.layout.addWidget(l2, 2, 0)
        self.layout.addWidget(self.out_t2, 2, 1)
        self.layout.addWidget(self.out_b, 2, 2)
        #self.layout.addItem(spacer, 2, 1)
        self.layout.addWidget(l6, 3, 0)
        self.layout.addWidget(l3, 4, 1)
        self.layout.addWidget(l32, 4, 2, 1, 2)
        self.layout.addWidget(l7, 5, 1)
        self.layout.addWidget(self.nb_vel_text, 5, 2, 1, 2)
        self.layout.addWidget(l8, 6, 1)
        self.layout.addWidget(self.manning_text, 6, 2, 1, 2)
        self.layout.addWidget(l4, 7, 1)
        self.layout.addWidget(self.inter, 7, 2, 1, 2)
        self.layout.addWidget(l5, 8, 1)
        self.layout.addWidget(self.nb_extrapro_text, 8, 2, 1, 2)
        #self.layout.addItem(spacer, 7, 1)
        self.layout.addWidget(self.load_b, 9, 2)
        self.layout.addWidget(self.cb, 9, 1)
        self.setLayout(self.layout)

    def load_mascaret_gui(self):
        """
        The function to load the mascaret data, calling mascaret.py
        :return:
        """
        # update the xml file of the project
        self.save_xml(0)
        self.save_xml(1)
        self.save_xml(2)
        path_im = self.find_path_im()
        self.send_log.emit(self.tr('# Load: Mascaret data.'))
        sys.stdout = self.mystdout = StringIO()
        [self.coord_pro, coord_r, self.xhzv_data, name_pro, name_reach, self.on_profile, self.nb_pro_reach]\
            = mascaret.load_mascaret(self.namefile[0], self.namefile[1], self.namefile[2], self.pathfile[0],\
                                     self.pathfile[1], self.pathfile[2])
        sys.stdout = sys.__stdout__
        self.send_err_log()
        self.send_log.emit("py    file1='" + self.namefile[0] + "'")
        self.send_log.emit("py    file2='" + self.namefile[1] + "'")
        self.send_log.emit("py    file3='" + self.namefile[2] + "'")
        self.send_log.emit("py    path1='" + self.pathfile[0] + "'")
        self.send_log.emit("py    path2='" + self.pathfile[1] + "'")
        self.send_log.emit("py    path3='" + self.pathfile[2] + "'")
        self.send_log.emit("py    [coord_pro, coord_r, xhzv_data, name_pro, name_reach, on_profile, nb_pro_reach] "
                           " =  mascaret.load_mascaret(file1, file2, file3, path1, path2, path3)\n")
        self.send_log.emit("restart LOAD_MASCARET")
        self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[0], self.namefile[0]))
        self.send_log.emit("restart    file2: " + os.path.join(self.pathfile[1], self.namefile[1]))
        self.send_log.emit("restart    file3: " + os.path.join(self.pathfile[2], self.namefile[2]))

        if self.cb.isChecked() and path_im != 'no_path':
            mascaret.figure_mascaret(self.coord_pro, coord_r, self.xhzv_data, self.on_profile, self.nb_pro_reach,
                                     name_pro, name_reach, path_im, [0, 1], [-1], [0])
        # velocity distibution
        try:
            self.manning1 = float(self.manning_text.text())
            self.np_point_vel = int(self.nb_vel_text.text())
        except ValueError:
            self.send_log.emit("Error: The manning value or the number of velocity point is not understood.")
        self.distribute_velocity()
        # grid and interpolation
        self.interpo_choice = self.inter.currentIndex()
        self.grid_and_interpo(self.cb.isChecked())

        self.save_hdf5()

        if self.cb.isChecked():
            self.show_fig.emit()


class River2D(SubHydroW):
    """
        The sub-windows which help to open the river 2ddata. Call the river2D loader and save the name
         of the files to the project xml file.
        """
    show_fig = pyqtSignal()

    def __init__(self, path_prj, name_prj):
        super().__init__(path_prj, name_prj)
        self.mystdout = None
        self.init_iu()

    def init_iu(self):
        # update attibute for rubbar 2d
        self.attributexml = ['river2d_data']
        self.model_type = 'RIVER2D'
        self.namefile = []
        self.pathfile = []
        self.extension = [['.cdg'], ['.cdg']]  # list of list in case there is more than one possible ext.
        self.nb_dim = 2

        # if there is the project file with river 2d info, update the label and attibutes
        self.was_model_loaded_before(0, True)

        # geometry and output data
        self.l1 = QLabel(self.tr('<b> Geometry and Output data </.b>'))
        self.list_f = QListWidget()
        self.add_file_to_list()
        self.cb = QCheckBox(self.tr('Show figures'), self)

        # button
        self.choodirb = QPushButton(self.tr("Add all .cdg files (choose dir)"))
        self.choodirb.clicked.connect(self.add_all_file)
        self.removefileb = QPushButton(self.tr("Remove file"))
        self.removefileb.clicked.connect(self.remove_file)
        self.removeallfileb = QPushButton(self.tr("Remove all files"))
        self.removeallfileb.clicked.connect(self.remove_all_file)
        self.addfileb = QPushButton(self.tr("Add file"))
        self.addfileb.clicked.connect(self.add_file_river2d)
        self.loadb = QPushButton(self.tr("Load all files and create hdf5"))
        self.loadb.clicked.connect(self.load_river2d_gui)

        # grid creation
        l2D1 = QLabel(self.tr('<b>Grid creation </b>'))
        l2D2 = QLabel(self.tr('2D MODEL - No new grid needed.'))

        # layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.l1, 0, 0)
        self.layout.addWidget(self.list_f, 1, 0, 2, 2)
        self.layout.addWidget(self.choodirb, 1, 2, 1, 2)
        self.layout.addWidget(self.addfileb, 2, 2)
        self.layout.addWidget(self.removefileb, 2, 3)
        self.layout.addWidget(self.removeallfileb, 3, 3)
        self.layout.addWidget(l2D1, 4, 0)
        self.layout.addWidget(l2D2, 4, 1, 1, 2)
        self.layout.addWidget(self.loadb, 5, 1)
        self.layout.addWidget(self.cb, 5, 0)
        self.setLayout(self.layout)

    def remove_file(self):
        """
        small function to remove a .cdg file to the list to be loaded
        :return:
        """
        i = self.list_f.currentRow()
        item = self.list_f.takeItem(i)
        item = None
        del self.namefile[i]
        del self.pathfile[i]

    def remove_all_file(self):
        """
        reove all files as you could expect
        :return:
        """
        # empty list
        self.namefile = []
        self.pathfile = []
        self.list_f.clear()

    def add_file_river2d(self):
        """
        A function which call show_dialog, oprepare some data for it and update the list
        :return:
        """
        if len(self.extension) == len(self.namefile):
            self.extension.append(self.extension[0])
            self.attributexml.append(self.attributexml[0])
        self.show_dialog(len(self.namefile))
        self.add_file_to_list()

    def add_file_to_list(self):
        """
        A function to add all file contained in self.namefile to the QWidgetlist
        :return:
        """
        self.list_f.clear()
        while len(self.extension) <= len(self.namefile):
            self.extension.append(self.extension[0])
            self.attributexml.append(self.attributexml[0])
        for i in range(0, len(self.namefile)):
                self.list_f.addItem(self.namefile[i])

    def add_all_file(self):
        """
        The function which find all .cdg file in one directory
        :return:
        """

        # get the directory
        dir_name = QFileDialog.getExistingDirectory()
        if dir_name == '':  # cancel case
            self.send_log.emit("Warning: No selected directory for river 2d\n")
            return
        # get all file with .cdg
        dirlist = np.array(os.listdir(dir_name))
        dirlsit0 = dirlist[0]
        listcdf = [e for e in dirlist if e[-4:] == self.extension[0][0]]
        # add them to name file, path file and extension
        self.namefile = self.namefile + listcdf
        self.pathfile = self.pathfile + [dir_name] * len(listcdf)
        # update list
        self.add_file_to_list()

    def load_river2d_gui(self):
        """
        The function to load the river 2d data
        :return:
        """

        xyzhv = []
        self.ikle_all_t = []
        self.point_c_all_t = []
        self.point_all_t = []
        self.send_log.emit(self.tr('# Load: River2D data.'))

        path_im = self.find_path_im()
        if len(self.namefile) == 0:
            self.send_log.emit("Warning: No file chosen.")
        for i in range(0, len(self.namefile)):
            # save each name in the project file, empty list on i == 0
            if i == 0:
                self.save_xml(i, False)
            else:
                self.save_xml(i, True)
            # load
            sys.stdout = self.mystdout = StringIO()
            [xyzhv_i, ikle_i, coord_c] = river2d.load_river2d_cdg(self.namefile[i], self.pathfile[i])
            sys.stdout = sys.__stdout__
            # if fail
            self.send_err_log()
            if len(xyzhv_i) == 1 and xyzhv_i[0] == -99:
                return
            xyzhv.append(xyzhv_i)
            self.point_all_t.append(xyzhv_i[:, :2])
            self.ikle_all_t.append(ikle_i)
            self.point_c_all_t.append(coord_c)
            self.inter_h_all_t.append(xyzhv_i[:, 3])
            self.inter_vel_all_t.append(xyzhv_i[:, 4])
            if self.cb.isChecked() and path_im != 'no_path' and i == 0:
                river2d.figure_river2d(xyzhv_i, ikle_i, path_im, i)

            # log
            self.send_log.emit("py    file1='" + self.namefile[i] + "'")
            self.send_log.emit("py    path1='" + self.pathfile[i] + "'")
            self.send_log.emit("py    [v, h, coord_p, coord_c, ikle] = river2d.load_river2d_cdg(file1, path1) \n")
            self.send_log.emit("restart LOAD_RIVER_2D")
            self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[i], self.namefile[i]))

        # TEMPORARY correction because we have only one grid for all reaches
        self.point_all_t = [self.point_all_t]
        self.point_c_all_t = [self.point_c_all_t]
        self.ikle_all_t = [self.ikle_all_t]
        self.inter_h_all_t = [self.inter_h_all_t]
        self.inter_vel_all_t = [self.inter_vel_all_t]

        self.save_hdf5()

        if self.cb.isChecked():
            self.show_fig.emit()


class Rubar1D(SubHydroW):
    """
    The sub-windows which help to open the rubar data. Call the rubar loader and save the name
     of the files to the project xml file.
    """
    show_fig = pyqtSignal()

    def __init__(self, path_prj, name_prj):
        super().__init__(path_prj, name_prj)
        self.inter = QComboBox()
        self.init_iu()

    def init_iu(self):

        # update attibute for hec-ras 1d
        self.attributexml = ['rubar_1dpro', 'data1d_rubar']
        self.model_type = 'RUBAR1D'
        self.extension = [[''], ['']]  # no useful extension in this case
        self.nb_dim = 1

        # if there is the project file with rubar geo info, update the label and attibutes
        self.was_model_loaded_before(0)
        self.was_model_loaded_before(1)

        # label with the file name
        self.geo_t2 = QLabel(self.namefile[0], self)
        self.out_t2 = QLabel(self.namefile[1], self)

        # geometry and output data
        l1 = QLabel(self.tr('<b> Geometry data </b>'))
        self.geo_b = QPushButton('Choose file (.rbe)', self)
        self.geo_b.clicked.connect(lambda: self.show_dialog(0))
        self.geo_b.clicked.connect(lambda: self.geo_t2.setText(self.namefile[0]))
        l2 = QLabel(self.tr('<b> Output data </b>'))
        self.out_b = QPushButton('Choose file \n (profil.X)', self)
        self.out_b.clicked.connect(lambda: self.show_dialog(1))
        self.out_b.clicked.connect(lambda: self.out_t2.setText(self.namefile[1]))

        # grid creation options
        l6 = QLabel(self.tr('<b>Grid creation </b>'))
        l3 = QLabel(self.tr('Velocity distribution'))
        l32 = QLabel(self.tr("Based on Manning's formula"))
        l7 = QLabel(self.tr("Nb. of velocity points by profile"))
        l8 = QLabel(self.tr("Manning coefficient"))
        l4 = QLabel(self.tr('Interpolation of the data'))
        l5 = QLabel(self.tr('Nb. of additional profiles'))
        self.inter.addItems(self.interpo)
        self.nb_extrapro_text = QLineEdit('1')
        self.nb_vel_text = QLineEdit('50')
        self.manning_text = QLineEdit('0.025')

        # load button
        self.load_b = QPushButton('Load data and create hdf5', self)
        self.load_b.clicked.connect(self.load_rubar1d)
        self.spacer1 = QSpacerItem(1, 20)
        self.spacer2 = QSpacerItem(1, 20)
        self.cb = QCheckBox(self.tr('Show figures'), self)

        # layout
        self.layout_hec = QGridLayout()
        self.layout_hec.addWidget(l1, 0, 0)
        self.layout_hec.addWidget(self.geo_t2,0, 1)
        self.layout_hec.addWidget(self.geo_b, 0, 2)
        self.layout_hec.addWidget(l2, 1, 0)
        self.layout_hec.addWidget(self.out_t2, 1, 1)
        self.layout_hec.addWidget(self.out_b, 1, 2)
        self.layout_hec.addItem(self.spacer1, 2, 1)
        self.layout_hec.addWidget(l6, 2, 0)
        self.layout_hec.addWidget(l3, 3, 1)
        self.layout_hec.addWidget(l32, 3, 2, 1, 2)
        self.layout_hec.addWidget(l7, 4, 1)
        self.layout_hec.addWidget(self.nb_vel_text, 4, 2, 1, 2)
        self.layout_hec.addWidget(l8, 5, 1)
        self.layout_hec.addWidget(self.manning_text, 5, 2, 1, 2)
        self.layout_hec.addWidget(l4, 6, 1)
        self.layout_hec.addWidget(self.inter, 6, 2, 1, 2)
        self.layout_hec.addWidget(l5, 7, 1)
        self.layout_hec.addWidget(self.nb_extrapro_text, 7, 2, 1, 2)
        #self.layout_hec.addItem(self.spacer2, 7, 1)
        self.layout_hec.addWidget(self.load_b, 8, 2)
        self.layout_hec.addWidget(self.cb, 8, 1)
        self.setLayout(self.layout_hec)


    def load_rubar1d(self):
        """
        A function to execture the loading and saving the the rubar file using rubar.py
        :return:
        """
        # update the xml file of the project
        self.save_xml(0)
        self.save_xml(1)
        path_im = self.find_path_im()
        if self.cb.isChecked() and path_im != 'no_path':
            self.save_fig = True
        #load rubar 1D
        sys.stdout = self.mystdout = StringIO()
        [self.xhzv_data, self.coord_pro, lim_riv] = rubar.load_rubar1d(self.namefile[0],
                                         self.namefile[1], self.pathfile[0], self.pathfile[1], path_im, self.save_fig)
        self.nb_pro_reach = [0, len(self.coord_pro)]   # should be corrected?
        sys.stdout = sys.__stdout__
        # log info
        self.send_log.emit(self.tr('# Load: Rubar 1D data.'))
        self.send_err_log()
        self.send_log.emit("py    file1='" + self.namefile[0] + "'")
        self.send_log.emit("py    file2='" + self.namefile[1] + "'")
        self.send_log.emit("py    path1='" + self.pathfile[0] + "'")
        self.send_log.emit("py    path2='" + self.pathfile[1] + "'")
        self.send_log.emit("py    [data_xhzv, coord_pro, lim_riv] = rubar.load_rubar1d(file1,"
                           " file2, path1, path2, '.', False)\n")
        self.send_log.emit("restart LOAD_RUBAR_1D")
        self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[0], self.namefile[0]))
        self.send_log.emit("restart    file2: " + os.path.join(self.pathfile[1], self.namefile[1]))

        # velocity distibution
        try:
            self.manning1 = float(self.manning_text.text())
            self.np_point_vel = int(self.nb_vel_text.text())
        except ValueError:
            self.send_log.emit("Error: The manning value or the number of velocity point is not understood.")
        # velcoity distribution
        self.distribute_velocity()
        # grid and interpolation
        self.interpo_choice = self.inter.currentIndex()
        self.grid_and_interpo(self.cb.isChecked())
        self.save_hdf5()

        if self.cb.isChecked() and path_im != 'no_path':
            self.show_fig.emit()


class HEC_RAS2D(SubHydroW):
    """
    The Qwidget which open the Hec-RAS data in 2D dimension
    """
    show_fig = pyqtSignal()

    def __init__(self, path_prj, name_prj):

        super().__init__(path_prj, name_prj)
        self.init_iu()

    def init_iu(self):

        # update attibutes
        self.attributexml = ['data2D']
        self.model_type = 'HECRAS2D'
        self.extension = [['.hdf']]
        self.nb_dim =2

        # if there is the project file with hecras info, update the label and attibutes
        self.was_model_loaded_before()
        self.h2d_t2 = QLabel(self.namefile[0], self)

        # geometry and output data
        l1 = QLabel(self.tr('<b> Geometry and output data </b>'))
        self.h2d_b = QPushButton('Choose file (.hdf, .h5)', self)
        self.h2d_b.clicked.connect(lambda: self.show_dialog(0))
        self.h2d_b.clicked.connect(lambda: self.h2d_t2.setText(self.namefile[0]))
        l2 = QLabel(self.tr('<b> Options </b>'))
        l3 = QLabel('All time step', self)
        l4 = QLabel('All flow area', self)

        # grid creation
        l2D1 = QLabel(self.tr('<b>Grid creation </b>'))
        l2D2 = QLabel(self.tr('2D MODEL - No new grid needed.'))

        # load button
        load_b = QPushButton('Load data and create hdf5', self)
        load_b.clicked.connect(self.load_hec_2d_gui)
        self.spacer = QSpacerItem(1, 80)
        self.cb = QCheckBox(self.tr('Show figures'), self)

        # layout
        self.layout_hec2 = QGridLayout()
        self.layout_hec2.addWidget(l1, 0, 0)
        self.layout_hec2.addWidget(self.h2d_t2, 0 , 1)
        self.layout_hec2.addWidget(self.h2d_b, 0, 2)
        self.layout_hec2.addWidget(l2, 1, 0)
        self.layout_hec2.addWidget(l3, 1, 1)
        self.layout_hec2.addWidget(l4, 1, 2)
        self.layout_hec2.addWidget(l2D1, 2, 0)
        self.layout_hec2.addWidget(l2D2, 2, 1, 1, 2)
        self.layout_hec2.addWidget(load_b, 3, 2)
        self.layout_hec2.addWidget(self.cb, 3, 1)
        self.layout_hec2.addItem(self.spacer, 4, 1)
        self.setLayout(self.layout_hec2)

    def load_hec_2d_gui(self):
        """
        The function which call the function which load hecras 2d and save name of file in the project file
         :return:
        """
        self.save_xml(0)
        path_im = self.find_path_im()
        # load the hec_ras data
        sys.stdout = self.mystdout = StringIO()
        [v, h, elev, coord_p, coord_c, ikle] = hec_ras2D.load_hec_ras2d(self.namefile[0], self.pathfile[0])
        sys.stdout = sys.__stdout__

        # TEMPORARY correction because we have only one grid for all time step
        self.point_all_t = [coord_p]
        self.point_c_all_t = [coord_c]
        self.ikle_all_t = [ikle]   # carefil ikle not corrected for non-triangular cells
        self.inter_h_all_t = v
        self.inter_vel_all_t = h

        # log info
        self.send_log.emit(self.tr('# Load: HEC-RAS 2D.'))
        self.send_err_log()
        self.send_log.emit("py    file1='" + self.namefile[0] + "'")
        self.send_log.emit("py    path1='" + self.pathfile[0] + "'")
        self.send_log.emit("py    [v, h, elev, coord_p, coord_c, ikle] = hec_ras2D.load_hec_ras2d(file1, path1)\n")
        self.send_log.emit("restart LOAD_HECRAS_2D")
        self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[0], self.namefile[0]))

        # save
        self.save_hdf5()

        if self.cb.isChecked() and path_im != 'no_path':
            hec_ras2D.figure_hec_ras2d(v, h, elev, coord_p, coord_c, ikle, path_im, [-1], [0])
            self.show_fig.emit()

class TELEMAC(SubHydroW):
    """
    The Qwidget which open the TELEMAC data
    """
    show_fig = pyqtSignal()

    def __init__(self, path_prj, name_prj):

        super().__init__(path_prj, name_prj)
        self.init_iu()

    def init_iu(self):

        # update the attibutes
        self.attributexml = ['telemac_data']
        self.model_type = 'TELEMAC'
        self.extension = [['.res', '.slf']]
        self.nb_dim = 2

        # if there is the project file with telemac info, update the label and attibutes
        self.was_model_loaded_before()
        self.h2d_t2 = QLabel(self.namefile[0], self)

        # geometry and output data
        l1 = QLabel(self.tr('<b> Geometry and output data </b>'))
        self.h2d_b = QPushButton('Choose file (.slf, .res)', self)
        self.h2d_b.clicked.connect(lambda: self.show_dialog(0))
        self.h2d_b.clicked.connect(lambda: self.h2d_t2.setText(self.namefile[0]))
        l2 = QLabel(self.tr('<b> Options </b>'))
        l3 = QLabel('All time steps', self)

        # grid creation
        l2D1 = QLabel(self.tr('<b>Grid creation </b>'))
        l2D2 = QLabel(self.tr('2D MODEL - No new grid needed.'))

        # load button
        load_b = QPushButton('Load data and create hdf5', self)
        load_b.clicked.connect(self.load_telemac_gui)
        self.spacer = QSpacerItem(1, 80)
        self.cb = QCheckBox(self.tr('Show figures'), self)

        # layout
        self.layout_hec2 = QGridLayout()
        self.layout_hec2.addWidget(l1, 0, 0)
        self.layout_hec2.addWidget(self.h2d_t2,0 , 1)
        self.layout_hec2.addWidget(self.h2d_b, 0, 2)
        self.layout_hec2.addWidget(l2, 1, 0)
        self.layout_hec2.addWidget(l3, 1, 1)
        self.layout_hec2.addWidget(l2D1, 2, 0)
        self.layout_hec2.addWidget(l2D2, 2, 1, 1, 2)
        self.layout_hec2.addWidget(load_b, 3, 2)
        self.layout_hec2.addItem(self.spacer, 4, 1)
        self.layout_hec2.addWidget(self.cb, 3, 1)
        self.setLayout(self.layout_hec2)

    def load_telemac_gui(self):
        """
        The function which call the function which load htelemac and save tje name of file in the project file
         :return:
        """
        self.save_xml(0)
        # load the telemac data
        path_im = self.find_path_im()
        sys.stdout = self.mystdout = StringIO()
        [v, h, coord_p, ikle, coord_c] = selafin_habby1.load_telemac(self.namefile[0], self.pathfile[0])
        sys.stdout = sys.__stdout__

        # TEMPORARY correction because we have only one grid for all time step and all reach
        self.point_all_t = [[coord_p]]
        self.point_c_all_t = [[coord_c]]
        self.ikle_all_t = [[ikle] ]  # carefil ikle not corrected for non-triangular cells
        self.inter_h_all_t = [v]
        self.inter_vel_all_t = [h]

        # log info
        self.send_log.emit(self.tr('# Load: TELEMAC data.'))
        self.send_err_log()
        self.send_log.emit("py    file1='" + self.namefile[0] + "'")
        self.send_log.emit("py    path1='" + self.pathfile[0] + "'")
        self.send_log.emit("py    [[v, h, coord_p, ikle] = selafin_habby1.load_telemac(file1, path1)\n")
        self.send_log.emit("restart LOAD_TELEMAC")
        self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[0], self.namefile[0]))

        # save
        self.save_hdf5()

        if self.cb.isChecked() and path_im != 'no_path':
            selafin_habby1.plot_vel_h(coord_p, h, v, path_im)
            self.show_fig.emit()



class SubstrateW(SubHydroW):
    """
    This is the widget used to load the substrate. It is practical to re-use some of the method from SubHydroW.
    So this class inherit from SubHydroW.
    """
    show_fig = pyqtSignal()

    def __init__(self, path_prj, name_prj):
        super().__init__(path_prj, name_prj)
        self.init_iu()

    def init_iu(self):

        # update attribute
        self.attributexml = ['substrate_data', 'att_name']
        self.model_type = 'SUBSTRATE'
        self.extension = [['.txt', '.shp', '.asc']]
        self.name_att = ''

        # if there was substrate info before, update the label and attibutes
        self.e2 = QLineEdit()
        self.was_model_loaded_before()
        self.get_att_name()
        self.h2d_t2 = QLabel(self.namefile[0], self)
        self.e2.setText(self.name_att)

        # label and button
        l1 = QLabel(self.tr('<b> Load substrate data </b>'))
        l2 = QLabel(self.tr('File'))
        l3 = QLabel(self.tr('If text file used as input:'))
        l7 = QLabel(self.tr('Attribute name:'))
        l6 = QLabel(self.tr('(only for shapefile)'))
        l5 = QLabel(self.tr('A Delaunay triangulation will be applied.'))
        self.h2d_b = QPushButton('Choose file (.txt, .shp)', self)
        self.h2d_b.clicked.connect(lambda: self.show_dialog(0))
        self.h2d_b.clicked.connect(lambda: self.h2d_t2.setText(self.namefile[0]))
        l4 = QLabel(self.tr('Default substrate:'))
        self.e1 = QLineEdit()
        # e1.setValidator(QIntValidator())
        load_b = QPushButton('Load data and save', self)
        load_b.clicked.connect(self.load_sub_gui)
        spacer = QSpacerItem(1, 140)
        spacer2 = QSpacerItem(150, 1)
        self.cb = QCheckBox(self.tr('Show figures'), self)

        #layout
        self.layout_sub = QGridLayout()
        self.layout_sub.addWidget(l1, 0, 0)
        self.layout_sub.addWidget(l2, 1, 0)
        self.layout_sub.addWidget(self.h2d_t2, 1, 1)
        self.layout_sub.addWidget(self.h2d_b, 1, 2)
        self.layout_sub.addWidget(l7, 2, 0)
        self.layout_sub.addWidget(self.e2, 2, 1)
        self.layout_sub.addWidget(l6, 2, 2)
        self.layout_sub.addWidget(l3, 4, 0)
        self.layout_sub.addWidget(l5, 4, 1)
        self.layout_sub.addWidget(l4, 3, 0)
        self.layout_sub.addWidget(self.e1, 3, 1)
        self.layout_sub.addWidget(load_b, 3, 2)
        self.layout_sub.addItem(spacer, 5, 0)
        self.layout_sub.addItem(spacer2, 5, 3)
        self.layout_sub.addWidget(self.cb, 3, 3)
        self.setLayout(self.layout_sub)

    def load_sub_gui(self):
        # save path and name substrate
        self.save_xml(0)
        # only save attribute name if shapefile
        self.name_att = self.e2.text()
        blob, ext = os.path.splitext(self.namefile[0])
        path_im = self.find_path_im()
        if ext == '.shp':
            if not self.name_att:
                self.send_log.emit("Error: No attribute name was given to load the shapefile.")
                return
            self.pathfile[1] = ''
            self.namefile[1] = self.name_att  # avoid to code things again
            self.save_xml(1)
        # load substrate
            sys.stdout = self.mystdout = StringIO()
            [coord_p, ikle_sub, sub_info] = substrate.load_sub_shp(self.namefile[0], self.pathfile[0], self.name_att)
            # log info
            self.send_log.emit(self.tr('# Load: Substrate data - Shapefile'))
            self.send_err_log()
            self.send_log.emit("py    file1='" + self.namefile[0] + "'")
            self.send_log.emit("py    path1='" + self.pathfile[0] + "'")
            self.send_log.emit("py    attr='" + self.name_att + "'")
            self.send_log.emit("py    [coord_p, ikle_sub, sub_info] = substrate.load_sub_shp(file1, path1, attr)\n")
            self.send_log.emit("restart LOAD_SUB_SHP")
            self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[0], self.namefile[0]))
            self.send_log.emit("restart    file2: " + os.path.join(self.pathfile[0], self.namefile[0]))
            self.send_log.emit("restart    attr: " + self.name_att)

            if self.cb.isChecked():
                substrate.fig_substrate(coord_p, ikle_sub, sub_info, path_im)
        elif ext == '.txt' or ext == ".asc":
            sys.stdout = self.mystdout = StringIO()
            [coord_pt, ikle_subt, sub_infot, x, y, sub] = substrate.load_sub_txt(self.namefile[0], self.pathfile[0])
            self.log_txt()
            if self.cb.isChecked():
                substrate.fig_substrate(coord_pt, ikle_subt, sub_infot, path_im, x, y, sub)
        else:
            self.send_log.emit("Warning: Unknown extension for substrate data, the model will try to load as .txt")
            sys.stdout = self.mystdout = StringIO()
            [coord_pt, ikle_subt, sub_infot, x, y, sub] = substrate.load_sub_txt(self.namefile[0], self.pathfile[0])
            if self.cb.isChecked():
                substrate.fig_substrate(coord_pt, ikle_subt, sub_infot, path_im, x, y, sub)
            self.log_txt()
        if self.cb.isChecked() and path_im != 'no_path':
            self.show_fig.emit()

    def log_txt(self):
        """
        The log for the substrate in text form. In a function because it is used twice
        :return:
        """
        # log info
        self.send_log.emit(self.tr('# Load: Substrate data - text file'))
        str_found = self.mystdout.getvalue()
        str_found = str_found.split('\n')
        for i in range(0, len(str_found)):
            if len(str_found[i]) > 1:
                self.send_log.emit(str_found[i])
        self.send_log.emit("py    file1='" + self.namefile[0] + "'")
        self.send_log.emit("py    path1='" + self.pathfile[0] + "'")
        self.send_log.emit("py    [coord_pt, ikle_subt, sub_infot, x, y, sub] = substrate.load_sub_txt(file1, path1)\n")
        self.send_log.emit("restart LOAD_SUB_TXT")
        self.send_log.emit("restart    file1: " + os.path.join(self.pathfile[0], self.namefile[0]))

    def get_att_name(self):
        """
        A function to get the attribute name of the shape file which is possibly int e project xml file.
        :return:
        """

        filename_path_pro = os.path.join(self.path_prj, self.name_prj + '.xml')
        if os.path.isfile(filename_path_pro):
            doc = ET.parse(filename_path_pro)
            root = doc.getroot()
            for i in range(0, len(self.attributexml)):
                child = root.find(".//" + self.attributexml[1])
                # if there is data in the project file about the model
                if child is not None:
                    self.name_att = child.text





