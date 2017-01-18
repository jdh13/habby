from io import StringIO
import os
from PyQt5.QtCore import QTranslator, pyqtSignal, Qt, QModelIndex
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QLabel, QGridLayout, QAction, qApp, \
    QTabWidget, QLineEdit, QTextEdit, QFileDialog, QSpacerItem, QListWidget,\
    QListWidgetItem, QMessageBox, QCheckBox
from PyQt5.QtGui import QPixmap
import time
import sys
from src import stathab_c
import xml.etree.ElementTree as ET


class StathabW(QWidget):
    """
    The class to load and manage the widget controlling the Stathab model.

    **Technical comments**

    The class StathabW makes the link between the data prepared by the user for Stathab and  the Stathab model
    which is in the src folder (stathab_c.py) using the graphical interface.  Most of the Stathab input are given in
    form of text file. For more info on the preparation of text files for stathab, read the document called
    'stathabinfo.pdf".  To use Stathab in HABBY, all Stathab input should be in the same directory. The user select
    this directory (using the button “loadb”) and HABBY tries to find the file it needs. All found files are added to
    the list called “file found”. If file are missing, they are added to the “file still needed” list.  The user can then
    select the fishes on which it wants to run stathab, then it run it by pressing on the “runb” button.

    If file where loaded before by the user in the same project, StathabW looks for them and load them again. Here we
    can have two cases: a) the data was saved in hdf5 format (as it is done when a stathab run was done) and the path
    to this file noted in the xml project file. b) Only the name of the directory was written in the xml project file,
    indicated that data was loaded but not saved in hdf5 yet. HABBY manages both cases.

    Next, we check in the xml project file where the folder to save the figure (path_im) is. In case, there are
    no path_im saved, Stathab create one folder to save the figure outputs. This should not be the usual case. Generally,
    path_im is created with the xml project file, but you cannot be sure.

    There is a list of error message which are there for the case where the data which was loaded before do not exist
    anymore. For example, somebody erased the directory with the Stathab data in the meantime.  In this case,
    a pop-up message open and warn the user.

    An important attribute of StathabW() is self.mystathab. This is an object fo the stahab class. The stathab model,
    which is in the form of a class and not a function, will be run on this object.
    """

    send_log = pyqtSignal(str, name='send_log')
    """
    A PyQtsignal used to write the log.
    """
    show_fig = pyqtSignal()
    """
    A PyQtsignal used to show the figures.
    """

    def __init__(self, path_prj, name_prj):

        super().__init__()

        self.path_prj = path_prj
        self.name_prj = name_prj
        self.path_im = os.path.join(self.path_prj, 'figures_habby')
        self.path_bio_stathab = './/biology'
        self.fish_selected = []
        self.dir_name = self.tr("No directory selected")
        self.mystdout = StringIO()
        self.msge = QMessageBox()
        self.firstitemreach = []  # the first item of a reach
        self.list_file = QListWidget()
        self.list_needed = QListWidget()
        self.list_s = QListWidget()
        self.list_re = QListWidget()
        self.list_f = QListWidget()
        # name of all the text file (see stathabinfo.pdf)
        self.listrivname = 'listriv.txt'
        self.end_file_reach = ['deb.txt', 'qhw.txt', 'gra.txt', 'dis.txt']
        self.name_file_allreach = ['bornh.txt', 'bornv.txt', 'borng.txt', 'Pref.txt']
        self.hdf5_name = self.tr('No hdf5 selected')
        self.mystathab = stathab_c.Stathab(self.name_prj, self.path_prj)
        self.dir_hdf5 = self.path_prj
        self.typeload = 'txt'  # txt or hdf5

        self.init_iu()

    def init_iu(self):

        # see if a directory was selected before for Stathab
        # see if an hdf5 was selected before for Stathab
        # if both are there, reload as the last time
        filename_prj = os.path.join(self.path_prj,self.name_prj + '.xml')
        if os.path.isfile(filename_prj):
            doc = ET.parse(filename_prj)
            root = doc.getroot()
            child = root.find(".//Stathab")
            if child is not None:
                dirxml = root.find(".//DirStathab")
                if dirxml is not None:
                    self.dir_name = dirxml.text
                hdf5xml = root.find(".//hdf5Stathab")
                if hdf5xml is not None:
                    self.hdf5_name = hdf5xml.text
                typeloadxml = root.find(".//TypeloadStathab")
                if typeloadxml is not None:
                    self.typeload = typeloadxml.text
        else:
            self.send_log.emit('Warning: Project was not saved. Save the project in the general tab \n')

        # check if there is a path where to save the figures
        if os.path.isfile(filename_prj):
            doc = ET.parse(filename_prj)
            root = doc.getroot()
            child = root.find(".//" + 'Path_Figure')
            if child is not None:
                self.path_im = child.text
        if not os.path.exists(self.path_im):
            os.makedirs(self.path_im)

        # prepare QLabel
        self.l1 = QLabel(self.tr('Stathab Input Files (.txt)'))
        loadb = QPushButton(self.tr("Select directory"))
        if len(self.dir_name) > 30:
            self.l0 = QLabel('...' + self.dir_name[-30:])
        else:
            self.l0 = QLabel(self.dir_name)
        l2 = QLabel(self.tr("Reaches"))
        self.l3 = QLabel(self.tr("File found"))
        self.l4 = QLabel(self.tr("File still needed"))
        l5 = QLabel(self.tr("Available Fish"))
        l6 = QLabel(self.tr("Selected Fish"))
        self.fishall = QCheckBox(self.tr('Select all fishes'), self)
        loadhdf5b = QPushButton(self.tr("Load data from hdf5"))
        self.runb = QPushButton(self.tr("Save and run Stathab"))
        self.cb = QCheckBox(self.tr('Show figures'), self)

        # connect method with list
        loadb.clicked.connect(self.select_dir)
        loadhdf5b.clicked.connect(self.select_hdf5)
        self.runb.clicked.connect(self.run_stathab_gui)
        self.list_re.itemClicked.connect(self.reach_selected)
        self.list_f.itemClicked.connect(self.add_fish)
        self.list_s.itemClicked.connect(self.remove_fish)
        self.fishall.stateChanged.connect(self.add_all_fish)

        # update label and list
        if self.dir_name != "No directory selected" and self.typeload == 'txt':
            if os.path.isdir(self.dir_name):
                self.load_from_txt_gui()
                if not self.mystathab.load_ok:
                    self.msge.setIcon(QMessageBox.Warning)
                    self.msge.setWindowTitle(self.tr("Stathab"))
                    self.msge.setText(self.mystdout.getvalue())
                    self.msge.setStandardButtons(QMessageBox.Ok)
                    self.msge.show()
            else:
                self.msge.setIcon(QMessageBox.Warning)
                self.msge.setWindowTitle(self.tr("Stathab"))
                self.msge.setText(self.tr("Stathab: The selected directory for stathab does not exist."))
                self.msge.setStandardButtons(QMessageBox.Ok)
                self.msge.show()
        if self.hdf5_name != 'No hdf5 selected' and self.typeload == 'hdf5':
            if os.path.isfile(self.hdf5_name):
                self.load_from_hdf5_gui()
                if not self.mystathab.load_ok:
                    self.msge.setIcon(QMessageBox.Warning)
                    self.msge.setWindowTitle(self.tr("Stathab"))
                    self.msge.setText(self.mystdout.getvalue())
                    self.msge.setStandardButtons(QMessageBox.Ok)
                    self.msge.show()
            else:
                self.msge.setIcon(QMessageBox.Warning)
                self.msge.setWindowTitle(self.tr("Stathab"))
                self.msge.setText(self.tr("Stathab: The selected hdf5 file for stathab does not exist."))
                self.msge.setStandardButtons(QMessageBox.Ok)
                self.msge.show()

        # Layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.l1, 0, 0)
        self.layout.addWidget(loadb, 0, 2)
        self.layout.addWidget(self.l0, 0, 1)
        self.layout.addWidget(l2, 1, 0)
        self.layout.addWidget(self.l3, 1, 1)
        self.layout.addWidget(self.l4, 1, 2)
        self.layout.addWidget(self.list_re, 2, 0)
        self.layout.addWidget(self.list_file, 2, 1)
        self.layout.addWidget(self.list_needed, 2, 2)
        self.layout.addWidget(l5, 3, 0)
        self.layout.addWidget(l6, 3, 1)
        self.layout.addWidget(loadhdf5b, 4, 2)
        self.layout.addWidget(self.list_f, 4, 0, 2,1)
        self.layout.addWidget(self.list_s, 4, 1, 2, 1)
        self.layout.addWidget(self.runb, 5, 2)
        self.layout.addWidget(self.fishall, 6, 1)
        self.layout.addWidget(self.cb, 6, 2)
        self.setLayout(self.layout)

    def select_dir(self):
        """
        This function is used to select the directory and find the files to laod stathab from txt files. It calls
        load_from_txt_gui() when done.


        """
        # get the directory
        self.dir_name = QFileDialog.getExistingDirectory()
        if self.dir_name == '':  # cancel case
            self.send_log.emit("Warning: No selected directory for stathab\n")
            return

        # clear all list
        self.mystathab = stathab_c.Stathab(self.name_prj, self.path_prj)
        self.list_re.clear()
        self.list_file.clear()
        self.list_s.clear()
        self.list_needed.clear()
        self.list_f.clear()
        self.fish_selected = []
        self.firstitemreach = []

        # save the directory in the project file
        filename_prj = os.path.join(self.path_prj, self.name_prj + '.xml')
        if not os.path.isfile(filename_prj):
            self.send_log.emit('Error: No project saved. Please create a project first in the General tab.')
            return
        else:
            doc = ET.parse(filename_prj)
            root = doc.getroot()
            child = root.find(".//Stathab")
            if child is None:
                stathab_element = ET.SubElement(root, "Stathab")
                dirxml = ET.SubElement(stathab_element, "DirStathab")
                dirxml.text = self.dir_name
                typeload = ET.SubElement(stathab_element, "TypeloadStathab")  # last load from txt or hdf5?
                typeload.text = 'txt'
            else:
                dirxml = root.find(".//DirStathab")
                if child is None:
                    dirxml = ET.SubElement(child, "DirStathab")
                    dirxml.text = self.dir_name
                else:
                    dirxml.text = self.dir_name
                dirxml = root.find(".//TypeloadStathab")
                if child is None:
                    dirxml = ET.SubElement(child, "TypeloadStathab")   # last load from txt or hdf5?
                    dirxml.text = 'txt'
                else:
                    dirxml.text = 'txt'
            doc.write(filename_prj)

            # fill the lists with the existing files
            self.load_from_txt_gui()

    def load_from_txt_gui(self):
        """
        The main roles of load_from_text_gui() are to call the load_function of the stathab class (which is in
        stathab_c.py in the folder src) and to call the function which create an hdf5 file. However, it does some
        modifications to the GUI before.

        **Technical comments**

        Here is the list of the modifications done to the graphical user interface before calling the load_function of
        Stathab.

        First, it updates the label. Because a new directory was selected, we need to update the label containing the
        directory’s name. We only show the 30 last character of the directory name. In addition, we also need to update
        the other label. Indeed, it is possible that the data used by Stathab would be loaded from an hdf5 file.
        In this case, the labels on the top of the list of file are slightly modified. Here, we insure that we are in
        the “text” version since we will load the data from text file.

        Next, it gets the name of all the reach and adds them to the list of reach name. For this, it calls a function
        from the stathab class (in src). Then, it looks which files are present and add them to the list which contains
        the reach name called self.list_re.

        Afterwards, it checks if the files needed by Stathab are here. The list of file is given in the
        self.end_file_reach list. The form of the file is always the name of the reach + one item of
        self.end_file_reach. If it does not find all files, it add the name of the files not found to self.list_needed,
        so that the user can be aware of which file he needs. The exception is Pref.txt. If HABBY do not find it in the
        directory, it uses the default “Pref.txt”. All files (apart from Pref.txt) should be in the same directory.

        Then, it calls a method of the Stathab class (in src) which reads the “pref.txt” file and adds the name
        of the fish to the GUI. Next, if all files are present, it loads the data using the method written in Stathab
        (in the src folder). When the data is loaded, it creates an hdf5 file from this data and save the name of this
        new hdf5 file in the xml project file (also using a method in the stathab class).

        Finally, it sends the log info as explained in the log section of the documentation
        """

        # update the labels
        if len(self.dir_name) > 30:
            self.l0.setText('...' + self.dir_name[-30:])
        else:
            self.l0.setText(self.dir_name)
        self.l1.setText(self.tr('Stathab Input Files (.txt)'))
        self.l3.setText(self.tr("File found"))
        self.l4.setText(self.tr("File still needed"))

        # read the reaches name
        sys.stdout = self.mystdout = StringIO()
        name_reach = stathab_c.load_namereach(self.dir_name, self.listrivname)
        sys.stdout = sys.__stdout__
        self.send_err_log()
        if name_reach == [-99]:
            self.list_re.clear()
            return
        for r in range(0, len(name_reach)):
            itemr = QListWidgetItem(name_reach[r])
            self.list_re.addItem(itemr)

        # see if the needed file are available
        # by reach
        c = -1
        for r in range(0, len(name_reach)):
            for i in range(0, len(self.end_file_reach)):
                file = os.path.join(self.dir_name, name_reach[r]+self.end_file_reach[i])
                if os.path.isfile(file):
                    itemf = QListWidgetItem(name_reach[r]+self.end_file_reach[i])
                    self.list_file.addItem(itemf)
                    c += 1
                else:
                    itemf = QListWidgetItem(name_reach[r]+self.end_file_reach[i])
                    self.list_needed.addItem(itemf)
                if i == 0: # note the first item to be able to highlight it afterwards
                    self.firstitemreach.append([itemf, c])

            self.list_file.addItem('----------------')
            c += 1

        # all reach
        # first choice> Pref.txt in dir_name is used.
        # default choice: Pref.txt in the biology folder.
        for i in range(0,len(self.name_file_allreach)):
            file = os.path.join(self.dir_name, self.name_file_allreach[i])
            if os.path.isfile(file):
                itemf = QListWidgetItem(self.name_file_allreach[i])
                self.list_file.addItem(itemf)
                itemf.setBackground(Qt.lightGray)
                # if a custom Pref.txt is present
                if i == len(self.name_file_allreach):
                    self.path_bio_stathab = self.dir_name
            else:
                # usual case: a file is missing
                if i != len(self.name_file_allreach)-1:
                    self.list_needed.addItem(self.name_file_allreach[i])
                # if Pref.txt is missing, let's use the default file
                else: # by default the biological model in the biology folder
                    file = os.path.join(self.path_bio_stathab, self.name_file_allreach[i])
                    if os.path.join(file):
                        itemf = QListWidgetItem(self.name_file_allreach[i] + ' (default)')
                        self.list_file.addItem(itemf)
                        itemf.setBackground(Qt.lightGray)
                    else:
                        self.list_needed.addItem(self.name_file_allreach[i])

        # read the available fish
        sys.stdout = self.mystdout = StringIO()
        [name_fish, blob] = stathab_c.load_pref(self.name_file_allreach[-1], self.path_bio_stathab)
        sys.stdout = sys.__stdout__
        self.send_err_log()
        if name_fish == [-99]:
            return
        for r in range(0, len(name_fish)):
            self.list_f.addItem(name_fish[r])

        # load now the text data
        if self.list_needed.count() > 0:
            self.send_log.emit('# Found part of the STATHAB files. Need re-load')
            return
        self.list_needed.addItem('All files found')
        self.send_log.emit('# Found all STATHAB files. Load Now.')
        sys.stdout = self.mystdout = StringIO()
        self.mystathab.load_stathab_from_txt('listriv.txt', self.end_file_reach, self.name_file_allreach, self.dir_name)
        self.mystathab.create_hdf5()

        # log info
        sys.stdout = sys.__stdout__
        self.send_err_log()
        if not self.mystathab.load_ok:
            self.send_log.emit('Error: Could not load stathab data.\n')
            return
        var1 = 'py    var1 = ['
        for i in range(0, len(self.end_file_reach)):
            var1 += "'" + self.end_file_reach[i] + "',"
        var1 = var1[:-1] + "]"
        self.send_log.emit(var1)
        var2 = 'py    var2 = ['
        for i in range(0, len(self.end_file_reach)):
            var2 += "'" + self.name_file_allreach[i] + "',"
        var2 = var2[:-1] + "]"
        self.send_log.emit(var2)
        self.send_log.emit("py    dir_name = '" + self.dir_name + "'")
        self.send_log.emit('py    mystathab = stathab_c.Stathab(name_prj, path_prj)')
        self.send_log.emit("py    mystathab.load_stathab_from_txt('listriv.txt', var1, var2, dir_name)")
        self.send_log.emit("py    self.mystathab.create_hdf5()")
        self.send_log.emit('restart LOAD_STATHAB_FROM_TXT_AND_CREATE_HDF5')

    def select_hdf5(self):
        """
        This function allows the user to choose an hsdf5 file as input from Stathab.

        **Technical comment**

        This function is for example useful if the user would have created an hdf5 file for a Stathab model in another
        project and he would like to send the same model on other fish species.

        This function writes the name of the new hdf5 file in the xml project file. It also notes that the last data
        loaded was of hdf5 type. This is useful when HABBY is restarting because it is possible to have a
        directory name and the address of an hdf5 file in the part of the xml project file concerning Stathab.
        HABBY should know if the last file loaded was this hdf5 or the files in the directory.
        Finally, it calls the function to load the hdf5 called load_from_hdf5_gui.
        """
        self.send_log.emit('# Load stathab file from hdf5.')

        # load the filename
        self.hdf5_name = QFileDialog.getOpenFileName()[0]
        self.dir_hdf5 = os.path.dirname(self.hdf5_name)
        if self.hdf5_name == '':  # cancel case
            self.send_log.emit("Warning: No selected hdf5 file for stathab\n")
            return
        blob, ext = os.path.splitext(self.hdf5_name)
        if ext != '.h5':
            self.send_log.emit("Warning: The file should be of hdf5 type.\n")

        # save the directory in the project file
        filename_prj = os.path.join(self.path_prj, self.name_prj + '.xml')
        if not os.path.isfile(filename_prj):
            self.send_log.emit('Error: No project saved. Please create a project first in the General tab.')
            return
        else:
            doc = ET.parse(filename_prj)
            root = doc.getroot()
            child = root.find(".//Stathab")
            if child is None:
                stathab_element = ET.SubElement(root, "Stathab")
                dirxml = ET.SubElement(stathab_element, "hdf5Stathab")
                dirxml.text = self.dir_name
                typeload = ET.SubElement(stathab_element, "TypeloadStathab")  # last load from txt or hdf5?
                typeload.text = 'hdf5'
            else:
                dirxml = root.find(".//hdf5Stathab")
                if dirxml is None:
                    dirxml = ET.SubElement(child, "hdf5Stathab")
                    dirxml.text = self.hdf5_name
                else:
                    dirxml.text = self.hdf5_name
                typeload = root.find(".//TypeloadStathab")
                if typeload is None:
                    typeload = ET.SubElement(child, "TypeloadStathab")   # last load from txt or hdf5?
                    typeload.text = 'hdf5'
                else:
                    typeload.text = 'hdf5'
            doc.write(filename_prj)

        # clear list of the GUI
        self.mystathab = stathab_c.Stathab(self.name_prj, self.path_prj)
        self.list_re.clear()
        self.list_file.clear()
        self.list_s.clear()
        self.list_needed.clear()
        self.fish_selected = []
        self.firstitemreach = []

        # load hdf5 data
        self.load_from_hdf5_gui()

    def load_from_hdf5_gui(self):
        """
        This function calls from the GUI the load_stathab_from_hdf5 function. In addition to call the function to load
        the hdf5, it also updates the GUI according to the info contained in the hdf5.

        **Technical comments**

        This functino updates the Qlabel similarly to the function “load_from_txt_gui()”.
        It also loads the data calling the load_stathab_from_hdf5 function from the Stathab class in src. The info
        contains in the hdf5 file are now in the memory in various variables called self.mystathab.”something”.
        HABBY used them to update the GUI. First, it updates the list which contains the name of the reaches
        (self.list_re.). Next, it checks that each of the variable needed exists and that they contain some data.
        Afterwards, HABBY looks which preference file to use. Either, it will use the default preference file
        (contained in HABBY/biology) or a custom preference prepared by the user. This custom preference
        file should be in the same folder than the hdf5 file. When the preference file was found, HABBY reads all
        the fish type which are described and add their name to the self.list_f list which show the available fish
        to the user in the GUI. Finally it checks if all the variables were found or if some were missing
        """
        # update QLabel
        self.l1.setText(self.tr('Stathab Input Files (.hdf5)'))
        if len(self.dir_name) > 30:
            self.l0.setText(self.hdf5_name[-30:])
        else:
            self.l0.setText(self.hdf5_name)
        self.l3.setText(self.tr("Data found"))
        self.l4.setText(self.tr("Data still needed"))

        # load data
        self.send_log.emit('# load stathab from hdf5.')
        sys.stdout = self.mystdout = StringIO()
        self.mystathab.load_stathab_from_hdf5()

        # log info
        sys.stdout = sys.__stdout__
        self.send_err_log()
        if not self.mystathab.load_ok:
            self.send_log.emit('Error: Data from  hdf5 not loaded.\n')
            return
        self.send_log.emit('py    mystathab = stathab_c.Stathab(name_prj, path_prj)')
        self.send_log.emit('py    mystathab.load_stathab_from_hdf5()')
        self.send_log.emit('restart LOAD_STATHAB_FROM_HDF5')

        # update list with name reach
        if len(self.mystathab.name_reach) == 0:
            self.send_log.emit('Error: No name of reach found. \n')
            return
        for r in range(0, len(self.mystathab.name_reach)):
            itemr = QListWidgetItem(self.mystathab.name_reach[r])
            self.list_re.addItem(itemr)

        # update list with name of data
        data_reach = [self.mystathab.qlist, self.mystathab.qwh, self.mystathab.disthmes,
                self.mystathab.qhmoy, self.mystathab.dist_gran]
        data_reach_str = ['qlist', 'qwh', 'dishhmes', 'qhmoy', 'dist_granulo']
        c = -1
        for r in range(0, len(self.mystathab.name_reach)):
            for i in range(0, 5):
                if data_reach[i]:
                    itemr = QListWidgetItem(data_reach_str[i])
                    self.list_file.addItem(itemr)
                    c +=1
                else:
                    self.list_needed.addItem(data_reach_str[i])
                if i == 0:  # note the first item to be able to highlight it afterwards
                    self.firstitemreach.append([itemr, c])
            c += 1
            self.list_file.addItem('----------------')

        # update list with bornes of velocity, height and granola
        lim_str = ['limits height', 'limits velocity', 'limits granulometry']
        for i in range(0, 3):
            if len(self.mystathab.lim_all[i]) > 1:
                itemr = QListWidgetItem(lim_str[i])
                self.list_file.addItem(itemr)
                itemr.setBackground(Qt.lightGray)
            else:
                self.list_needed.addItem(lim_str[i])

        # see if a preference file is available in the same folder than the hdf5 file
        preffile = os.path.join(self.dir_hdf5, self.name_file_allreach[3])
        if os.path.isfile(preffile):
            self.path_bio_stathab = self.dir_hdf5
            itemp = QListWidgetItem(self.name_file_allreach[3])
            self.list_file.addItem(itemp)
            itemp.setBackground(Qt.lightGray)
        else:
            itemp = QListWidgetItem(self.name_file_allreach[3] + '(default)')
            self.list_file.addItem(itemp)
            itemp.setBackground(Qt.lightGray)

        # read the available fish
        sys.stdout = self.mystdout = StringIO()
        [name_fish, blob] = stathab_c.load_pref(self.name_file_allreach[3], self.path_bio_stathab)
        sys.stdout = sys.__stdout__
        self.send_err_log()
        if name_fish == [-99]:
            return
        for r in range(0, len(name_fish)):
            self.list_f.addItem(name_fish[r])

        # final check
        if self.list_needed.count() == 0:
            self.list_needed.addItem('All hdf5 data found')
            self.send_log.emit('# Found all STATHAB files.')
        else:
            self.send_log.emit('# Found part of the STATHAB files. Need to re-load.')
            return

    def reach_selected(self):
        """
        A function which indcates which files are linked with which reach.

        **Technical comment**

        This is a small function which only impacts the GUI. When a Stathab model has more than one reach,
        the user can click on the name of the reach. When he does this, HABBY selects the first file linked
        with this reach and shows it in self.list_f. This first file is highlighted and the list is scrolled
        down so that the files linked with the selected reach are shown. This function manages this. It is connected
        with the list self.list_re, which is the list with the name of the reaches.

        """
        [item_sel, r] = self.firstitemreach[self.list_re.currentRow()]
        self.list_file.setCurrentRow(r)
        self.list_file.scrollToItem(item_sel)

    def send_err_log(self):
        """
        Send the errors and warnings to the logs. It is useful to note that the stdout was redirected to self.mystdout.
        """
        str_found = self.mystdout.getvalue()
        str_found = str_found.split('\n')
        for i in range(0, len(str_found)):
            if len(str_found[i]) > 1:
                self.send_log.emit(str_found[i])

    def add_fish(self):
        """
        This function add the name of one fish species to the selected list of fish species.
        """
        items = self.list_f.selectedItems()
        if items:
            for i in range(0,len(items)):
                # avoid to have the same fish multiple times
                if items[i].text() in self.fish_selected:
                    pass
                else:
                    self.list_s.addItem(items[i].text())
                    self.fish_selected.append(items[i].text())

    def remove_fish(self):
        """
        This function remove the name of one fish species to the selected list of fish species.
        """

        item = self.list_s.takeItem(self.list_s.currentRow())
        self.fish_selected.remove(item.text())
        item = None

    def add_all_fish(self):
        """
        This function add the name of all known fish (the ones in Pref.txt) to the QListWidget.
        """
        if self.fishall.isChecked():

            items = []
            for index in range(self.list_f.count()):
                items.append(self.list_f.item(index))
            if items:
                for i in range(0, len(items)):
                    # avoid to have the same fish multiple times
                    if items[i].text() in self.fish_selected:
                        pass
                    else:
                        self.list_s.addItem(items[i].text())
                        self.fish_selected.append(items[i].text())

    def run_stathab_gui(self):
        """
        This is the function which calls the function to run the Stathab model.  First it read the list called
        self.list_s. This is the list with the fishes selected by the user. Then, it calls the function to run
        stathab and the one to create the figure if the figures were asked by the user. Finally, it writes the log.
        """
        self.send_log.emit('# Run Stathab from loaded data')
        # get the chosen fish
        self.mystathab.fish_chosen = []
        fish_list = []
        if self.list_s.count() == 0:
            self.send_log.emit('Error: no fish chosen')
            return
        for i in range(0, self.list_s.count()):
            fish_item = self.list_s.item(i)
            fish_item_str = fish_item.text()
            self.mystathab.fish_chosen.append(fish_item_str)
        sys.stdout = self.mystdout = StringIO()
        # run stathab
        self.mystathab.stathab_calc(self.path_bio_stathab, self.name_file_allreach[3])
        sys.stdout = sys.__stdout__
        self.send_err_log()
        # save data and fig
        self.mystathab.path_im = self.path_im
        self.mystathab.savetxt_stathab()
        if self.cb.isChecked():
            self.mystathab.savefig_stahab()
            self.show_fig.emit()

        # log information
        sys.stdout = sys.__stdout__
        self.send_err_log()
        if len(self.mystathab.disthmes[0]) == 1:
            if self.mystathab.disthmes[0] == -99:
                return
        self.send_log.emit("py    path_bio = '" + self.path_bio_stathab + "'")
        self.send_log.emit("py    mystathab.stathab_calc(path_bio)")
        self.send_log.emit("py    mystathab.savetxt_stathab()")
        self.send_log.emit("py    mystathab.path_im = '.'")
        self.send_log.emit("py    mystathab.savefig_stahab()")
        self.send_log.emit("restart    RUN_STATHAB_AND_SAVE_RESULTS")

