"""
This file is part of the free software:
 _   _   ___  ______________   __
| | | | / _ \ | ___ \ ___ \ \ / /
| |_| |/ /_\ \| |_/ / |_/ /\ V /
|  _  ||  _  || ___ \ ___ \ \ /
| | | || | | || |_/ / |_/ / | |
\_| |_/\_| |_/\____/\____/  \_/

Copyright (c) IRSTEA-EDF-AFB 2017-2018

Licence CeCILL v2.1

https://github.com/YannIrstea/habby

"""
import numpy as np
import os
import time
import glob
import difflib
import matplotlib
import filecmp
from copy import deepcopy
matplotlib.use("qt5agg")
import matplotlib.pyplot as plt
from src import selafin_habby1
from src import mascaret
from src import Hec_ras06
from src import rubar
from src import sw2d
from src import iber2d
from src import river2d
from src import load_hdf5
from shutil import copyfile
from src import hec_ras2D
from src import estimhab
from src import stathab_c
from src import substrate
from src import fstress
from src import calcul_hab
from src import bio_info
from src import mesh_grid2
from src import lammi
from src import hydraulic_chronic
from src_GUI import output_fig_GUI


def all_command(all_arg, name_prj, path_prj, path_bio, option_restart=False, erase_id=True):
    """
    This function is used to call HABBY from the command line. The general form is to call:
    habby_cmd command_name input1 input2 .. input n. The list of the command_name is given in the documentation and by
    calling the command "python habby_cmd.py LIST_COMMAND". This functiion is usually called direclty by the main()
    or it is called by the function restart which read a list of function line by line. Careful, new command cannot
    contain the symbol ":" as it is used by restart.

    For the restart function, it is also important that the input folder is just in the folder "next" to the restart
    path. So the folder should not be moved randolmy inside the project folder or renamed.

    :param all_arg: the list of argument (sys.argv more or less)
    :param name_prj: the name of the project, created by default by the main()
    :param path_prj: the path to the project created by default by the main()
    :param path_bio: the path to the project
    :param option_restart: If True the command are coming from a restart log (which have an impact on file name and
           location)
    :param erase_id: If True, the files with the same name are erased in merge. If False, they are kept with a
           time stamp
    """
    # all_arg[0] is the script name (habby_cmd.py)

    # manage the folders for the restart case
    input_file = False
    path_input = ''
    if option_restart:
        path_input = os.path.join(os.path.dirname(path_prj), 'input')
        if not os.path.isdir(path_input):
            input_file = False
            print('Warning: Input folder not found for the restart function. We will use the absolute path given in the'
                  'restart file.')
        else:
            input_file = True
            print('Input folder found for the restart function.')

    # check if the path given are ok
    if not os.path.isdir(path_prj):
        print('Error: the path to the project does not exists \n')
        return
    file_prof = os.path.join(path_prj, name_prj + '.xml')
    if not os.path.isfile(file_prof):
        print('Error: the xml project is not found \n')
        return
    if not os.path.isdir(path_bio):
        print('Error: the path to the biological folder is not found \n')
        return

    # ----------------------------------------------------------------------------------

    if all_arg[1] == 'LIST_COMMAND':
        print("Here are the available command for habby:")
        print('\n')
        print("LOAD_HECRAS_1D: load the hec-ras data in 1D. Input: name of .geo, name of the data file, interpolation "
              "choice,(number of profile to add), (output name)")
        print("LOAD_HECRAS_2D: load the hec-ras data in 2D. Input: name of the .h5 file, (output name)")
        print('LOAD_HYDRO_HDF5: load an hydrological hdf5. Input: the name of the hdf5 (with the path)')
        print("LOAD_MASCARET: load the mascaret data. Input: name of the three inputs files - xcas, geo, opt, "
              "manning coefficient, interpolation choice, (number of profile to add), (output name), (nb_point_vel=x)")
        print("LOAD_RIVER_2D: load the river 2d data. Input: folder containing the cdg file, (output name)")
        print("LOAD_RUBAR_1D: load the Rubar data in 1D. Input: name of input file .rbe, name of the profile input "
              "file, manning coefficient, interpolation choice, (number of profile to add), (output name),"
              "(nb_point_vel=x)")
        print("LOAD_RUBAR_2D: load the Rubar data in 2D. Input: name of .dat or .mai file, name of input .tps file "
              "(output name)")
        print("LOAD_SW2D: load the SW2D dataD. Input: name of .geo file, name of input .res file "
              "(output name)")
        print("LOAD_IBER2D: load the IBER2D dataD. Input: name of .dat file, name of input .rep files "
              "(output name)")
        print("LOAD_TELEMAC: load the telemac data. Input: name of the .res file, (output name)")
        print("LOAD_LAMMI: load lammi data. Input: the name of the folder containing transect.txt and facies.txt and "
              "the name of the folder with the HydroSim result, (output name)")

        print('\n')
        print('MERGE_GRID_SUB: merge the hydrological and substrate grid together. Input: the name of the hydrological hdf5'
              ', the name of the substrate hdf5, the default data for the substrate (in cemagref code), (output name)')
        print('LOAD_SUB_SHP: load the substrate from a shapefile. Input: filename of the shapefile,'
              'code_type as Cemagref or Sandre, (dominant_case as 1 or -1)')
        print('LOAD_SUB_TXT: load the substrate from a text file. Input: filename of the texte file,'
              'code_type as Cemagref or Sandre')
        print('LOAD_SUB_CONST: Create and hdf5 with a constant substrate. Code_type Cemagref Input: value of the '
              'substrate between 1 and 8.  (output name with path). The value 0 results in all possible substrate '
              'value to be loaded')
        print('LOAD_SUB_HDF5: load the substrate data in an hdf5 form. Input: the name of the hdf5 file (with path)')
        print('CREATE_RAND_SUB: create a random substrate shapefile. Will be created  in the cemagref code in the '
              'type coarser?dominant/... Input: the name of the hydrological hdf5 file (with path), (output name)')

        print('\n')
        print('RUN_ESTIMHAB: Run the estimhab model. Input: qmes1 qmes2 wmes1 wmes2 h1mes h2mes q50 qmin qmax sub'
              '- all data in float')
        print('RUN_HABITAT: Estimate the habitat value from an hdf5 merged files. It used the coarser substrate '
              'as the substrate layer if the parameter run_choice is zero. We can also choose to make the calculation'
              'on the dominant substrate (run_choice:1) or the substrate by percentage (run_choice:2). The chosen stage'
              'mshould be separated by a comma.If the keyword all is given as the chosen stage, all available stage '
              'will be used. To get the calculation on more than one fish species, separate the names of '
              'the xml biological files by a comma without a space between the command and the filenames. '
              'Input: pathname of merge file, name of xml prefence file with no path, stage_chosen,'
              ' run_choice.' )
        print('HYDRO_CHRONIC: hydrological chronicle. Create a new merge file for the chosen output discharge. The'
              'output discharges should be in the range of the input discharge. Input: list of the names of the merge '
              'file without path , list of input discharge, list of output discharge, minimum water height')
        print('RUN_FSTRESS: Run the fstress model. Input: the path to the files list_riv, deb, and qwh.txt and'
              ' (path where to save output)')
        print("RUN_STATHAB: Run the stathab model. Input: the path to the folder with the different input files, "
              "(the river type, 0 by default, 1, or 2 for tropical rivers).")
        print("ADD_HYDRO_HDF5: Add hdf5 filas with hydraulic data together in one hydraulic hdf5. The number of time"
              " step should be the same in all files. No substrate data. Input: the name of the first hdf5 (with path),"
              " the name of the second hdf5 file, (name of other hdf5 files as needed)")
        print("ADD_MERGE_HDF5: Add hdf5 failes with merge data together in one merge hdf5. Substrate data available. "
              "The number of time step should be the same in both file. Input: the name of the first hdf5 (with path),"
              " the name of the second hdf5 file, (name of other hdf5 files as needed)")

        print('\n')
        print("RESTART: Relauch HABBY based on a list of command in a text file (restart file) Input: the name of file"
              " (with the path).")
        print("ALL: if the keywork ALL is followed by a command from HABBY, the command will be applied to all file"
              " in a folder. The name of the input file should be in the form: path_to_folder/*.ext with the "
              "right extension as ext. No output name should be given.")
        print("COMPARE_TEST: Call the small function which compare the files in two folders. Useful to test habby "
              "output. Input: The path to the folder with the reference file, the path to the folder with the "
              "files to check")

        print('\n')
        print('list of options which can be added after the command: (1) path_prj= path to project, (2) '
              'name_prj= name of the project, (3) path_bio: the path to the biological files')

# ------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_TELEMAC':
        # check
        if not 2 < len(all_arg) < 5:
            print('The function LOAD_TELEMAC needs one or two inputs, the .res file name and the output name.')
            return
        # get filename
        filename = all_arg[2]
        if not input_file:
            pathfilet = os.path.dirname(filename)
        else:
            pathfilet = path_input
        namefilet = os.path.basename(filename)

        # hdf5
        if len(all_arg) == 4:
            namepath_hdf5 = all_arg[3]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)
        else:
            name_hdf5 = 'Hydro_TELEMAC_' + os.path.splitext(namefilet)[0]
            path_hdf5 = path_prj

        selafin_habby1.load_telemac_and_cut_grid(name_hdf5, namefilet, pathfilet, name_prj, path_prj, 'TELEMAC',2,
                                                 path_hdf5,[], True)

# ------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_HECRAS_1D':
        if not 4 < len(all_arg) < 8:
            print('The function LOAD_HECRAS needs three to five inputs. Call LIST_COMMAND for more '
                  'information.')
            return

        # get filename
        filename_geo = all_arg[2]
        filename_data = all_arg[3]

        if not input_file:
            pathfile = [os.path.dirname(filename_geo), os.path.dirname(filename_data)]
        else:
            pathfile = [path_input, path_input]
        namefile = [os.path.basename(filename_geo), os.path.basename(filename_data)]

        # hdf5 and pro_add
        pro_add_is_here = False
        if len(all_arg) == 5:  # .py com f1 f2 int_type
            name_hdf5 = 'Hydro_HECRAS1D_' + os.path.splitext(namefile[0])[0]
            path_hdf5 = path_prj
        if len(all_arg) == 6:  # .py com f1 f2 int_type pro_add or .py com f1 f2 int_type output
            try:
                pro_add_is_here = True
                pro_add = int(all_arg[5])
            except ValueError:
                pass
            if not pro_add_is_here:
                namepath_hdf5 = all_arg[5]
                name_hdf5 = os.path.basename(namepath_hdf5)
                path_hdf5 = os.path.dirname(namepath_hdf5)
            else:
                name_hdf5 = 'Hydro_HECRAS1D_' + os.path.splitext(namefile[0])[0]
                path_hdf5 = path_prj
        if len(all_arg) == 7:   # .py com f1 f2 int_type pro_add output
            pro_add_is_here = True
            pro_add = int(all_arg[5])
            namepath_hdf5 = all_arg[6]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)

        # interpo
        try:
            inter = int(all_arg[4])
        except ValueError:
            print('Error: Interpolation type should be 0, 1, 2')
            return

        if pro_add_is_here:
            Hec_ras06.open_hec_hec_ras_and_create_grid(name_hdf5, path_hdf5, name_prj, path_prj, 'HECRAS1D', namefile,
                                                       pathfile,inter , '.', False, pro_add,[], True)
        else:
            Hec_ras06.open_hec_hec_ras_and_create_grid(name_hdf5, path_hdf5, name_prj, path_prj, 'HECRAS1D', namefile,
                                                       pathfile, inter, '.', False, 5 , [] , True)

# --------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_HECRAS_2D':
        if not 2 < len(all_arg) < 5:
            print('The function LOAD_HECRAS_2D needs one or two inputs, the .res file name and the output name.')
            return
        # get filename
        filename = all_arg[2]
        if not input_file:
            pathfile = os.path.dirname(filename)
        else:
            pathfile= path_input
        namefile = os.path.basename(filename)

        if len(all_arg) == 4:
            namepath_hdf5 = all_arg[3]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)
        else:
            name_hdf5 = 'Hydro_HECRAS2D_' + os.path.splitext(namefile)[0]
            path_hdf5 = path_prj
        hec_ras2D.load_hec_ras_2d_and_cut_grid(name_hdf5, filename, pathfile, name_prj, path_prj, 'HECRAS2D', 2,
                                               path_hdf5, [], True)

# ------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_RUBAR_2D':
        if not 3 < len(all_arg) < 6:
            print('The function LOAD_RUBAR_2D needs two to three inputs. Call LIST_COMMAND for more '
                  'information.')
            return

        filename_geo = all_arg[2]
        filename_data = all_arg[3]
        if not input_file:
            pathgeo = os.path.dirname(filename_geo)
            pathtps = os.path.dirname(filename_data)
        else:
            pathgeo = path_input
            pathtps = path_input
        geofile = os.path.basename(filename_geo)
        tpsfile = os.path.basename(filename_data)

        if len(all_arg) == 4:
            name_hdf5 = 'Hydro_RUBAR2D_' + os.path.splitext(geofile[0])[0]
            path_hdf5 = path_prj
        if len(all_arg) == 5:
            namepath_hdf5 = all_arg[4]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)

        rubar.load_rubar2d_and_create_grid(name_hdf5, geofile, tpsfile, pathgeo, pathtps, '.', name_prj, path_prj,
                                           'RUBAR2D', 2, path_hdf5,[], False)

# ------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_SW2D':
        if not 3 < len(all_arg) < 6:
            print('The function LOAD_SW2D needs two to three inputs.\
                   Call LIST_COMMAND for more information.')
            return

        filename_geo = all_arg[2]
        filename_data = all_arg[3]
        if not input_file:
            pathgeo = os.path.dirname(filename_geo)
            pathtps = os.path.dirname(filename_data)
        else:
            pathgeo = path_input
            pathtps = path_input
        geofile = os.path.basename(filename_geo)
        tpsfile = os.path.basename(filename_data)

        if len(all_arg) == 4:
            name_hdf5 = 'Hydro_SW2D_' + os.path.splitext(geofile[0])[0]
            path_hdf5 = path_prj
        if len(all_arg) == 5:
            namepath_hdf5 = all_arg[4]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)

        sw2d.load_sw2d_and_modify_grid(name_hdf5, geofile, tpsfile, pathgeo,
                                       pathtps, '.', name_prj, path_prj,
                                       'SW2D', 2, path_hdf5, [], False)

# ------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_IBER2D':
        if not 6 < len(all_arg) < 9:
            print('The function LOAD_SW2D needs seven to eight inputs.\
                   Call LIST_COMMAND for more information.')
            return

        filename_geo = all_arg[2]
        filename_data1 = all_arg[3]
        filename_data2 = all_arg[4]
        filename_data3 = all_arg[5]
        filename_data4 = all_arg[6]
        if not input_file:
            pathgeo = os.path.dirname(filename_geo)
            pathtps = os.path.dirname(filename_data1)
        else:
            pathgeo = path_input
            pathtps = path_input
        geofile = os.path.basename(filename_geo)
        tpsfile1 = os.path.basename(filename_data1)
        tpsfile2 = os.path.basename(filename_data2)
        tpsfile3 = os.path.basename(filename_data3)
        tpsfile4 = os.path.basename(filename_data4)

        if len(all_arg) == 7:
            name_hdf5 = 'Hydro_IBER2D_' + os.path.splitext(geofile[0])[0]
            path_hdf5 = path_prj
        if len(all_arg) == 8:
            namepath_hdf5 = all_arg[7]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)

        iber2d.load_iber2d_and_modify_grid(name_hdf5, geofile, tpsfile1,
                                           tpsfile2, tpsfile3, tpsfile4,
                                           pathgeo, pathtps, '.', name_prj,
                                           path_prj, 'IBER2D', 2, path_hdf5,
                                           [], False)

# ------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_MASCARET':
        if not 6 < len(all_arg) < 11:
            print('The function LOAD_MASCARET needs five to eight inputs. Call LIST_COMMAND for more '
                  'information.')
            return
        pro_add_is_here = False
        pro_add = 1

        # get filename
        filename_gen = all_arg[2]
        filename_geo = all_arg[3]
        filename_data = all_arg[4]
        if not input_file:
            pathfile = [os.path.dirname(filename_gen), os.path.dirname(filename_geo), os.path.dirname(filename_data)]
        else:
            pathfile = [path_input, path_input, path_input]
        namefile = [os.path.basename(filename_gen), os.path.basename(filename_geo), os.path.basename(filename_data)]

        # get nb_point_vel
        nb_point_vel = 70
        for i in range(5, len(all_arg)):
            if all_arg[i][:13] == 'nb_point_vel=':
                try:
                    nb_point_vel = str(all_arg[i][13:])
                except ValueError:
                    print('The number of velcoity point is not an int. Should be of the form nb_point_vel=x')
                    return
                del all_arg[i]
                break

        # get the manning data 9can be a float or the name of a text file
        manning_data = all_arg[5]
        try:
            manning_data = float(manning_data)
        except ValueError:
            if option_restart:
                manning_data = os.path.join(path_input, os.path.basename(manning_data))
            if os.path.isfile(manning_data):
                manning_data = load_manning_txt(manning_data)
            else:
                print('Manning data should be a float or the name of text file')
                return

        # get the interpolation type
        try:
            inter = int(all_arg[6])
        except ValueError:
            print('Error: Interpolation type should be 0, 1, 2')
            return

        # get the  hdf5 name
        if len(all_arg) == 7:  # .py com f1 f2 f3 int_type
            name_hdf5 = 'Hydro_MASCARET_' + os.path.splitext(namefile[0])[0]
            path_hdf5 = path_prj
        if len(all_arg) == 8:  # .py com f1 f2 f3 int_type pro_add or .py com f1 f2 f3 int_type output
            try:
                pro_add_is_here = True
                pro_add = int(all_arg[7])
            except ValueError:
                pass
            if not pro_add_is_here:
                namepath_hdf5 = all_arg[7]
                name_hdf5 = os.path.basename(namepath_hdf5)
                path_hdf5 = os.path.dirname(namepath_hdf5)
            else:
                name_hdf5 = 'Hydro_MASCARET_' + os.path.splitext(namefile[0])[0]
                path_hdf5 = path_prj
        if len(all_arg) == 9:
            pro_add_is_here = True
            pro_add = int(all_arg[7])
            namepath_hdf5 = all_arg[8]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)

        # load mascaret
        mascaret.load_mascaret_and_create_grid(name_hdf5, path_hdf5, name_prj, path_prj, 'mascaret', namefile, pathfile,
                                               inter, manning_data, nb_point_vel, False, pro_add, [], path_hdf5, True)

# --------------------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_RIVER_2D':
        if not 2 < len(all_arg) < 5:
            print('The function LOAD_RIVER_2D needs one or two inputs. Call LIST_COMMAND for more '
                  'information.')
            return

        if not input_file:
            if os.path.isdir(all_arg[2]):
                filenames = load_hdf5.get_all_filename(all_arg[2], '.cdg')
            else:
                print('the input directory does not exist.')
                return
        else:
            if os.path.isdir(path_input):
                filenames = load_hdf5.get_all_filename(path_input, '.cdg')
            else:
                print('the input directory does not exist.')
                return

        paths = []
        for i in range(0, len(filenames)):
            paths.append(all_arg[2])

        if len(all_arg) == 3:
            name_hdf5 = 'Hydro_RIVER2D_' + os.path.splitext(filenames[0])[0]
            path_hdf5 = path_prj
        if len(all_arg) == 4:
            namepath_hdf5 = all_arg[3]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)

        river2d.load_river2d_and_cut_grid(name_hdf5, filenames, paths, name_prj, path_prj, 'RIVER2D', 2,
                                          path_hdf5, [], True)

# -------------------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_RUBAR_1D':
        if not 5 < len(all_arg) < 10:
            print('The function LOAD_RUBAR_1D needs four to seven inputs. Call LIST_COMMAND for more '
                  'information.')
            return
        pro_add_is_here = False

        # get filename
        filename_geo = all_arg[2]
        filename_data = all_arg[3]
        if not input_file:
            pathfile = [os.path.dirname(filename_geo), os.path.dirname(filename_data)]
        else:
            pathfile = [path_input, path_input]
        namefile = [os.path.basename(filename_geo), os.path.basename(filename_data)]

        # get nb_point_vel
        nb_point_vel = 70
        for i in range(5, len(all_arg)):
            if all_arg[i][:13] == 'nb_point_vel=':
                try:
                    nb_point_vel = str(all_arg[i][13:])
                except ValueError:
                    print('The number of velcoity point is not an int. Should be of the form nb_point_vel=x')
                    return
                del all_arg[i]
                break

        # get the manning data 9can be a float or the name of a text file
        manning_data = all_arg[4]
        try:
            manning_data = float(manning_data)
        except ValueError:
            if option_restart:
                manning_data = os.path.join(path_input, os.path.basename(manning_data))
            if os.path.isfile(manning_data):
                manning_data = load_manning_txt(manning_data)
            else:
                print('Manning data should be a float or the name of text file')
                return

        # get the interpolatin type and hdf5 name
        if len(all_arg) == 5:  # .py com f1 f2 int_type
            name_hdf5 = 'Hydro_RUBAR1D_' + os.path.splitext(namefile[0])[0]
            path_hdf5 = path_prj
        if len(all_arg) == 6:  # .py com f1 f2 int_type pro_add or .py com f1 f2 int_type output
            try:
                pro_add_is_here = True
                pro_add = int(all_arg[5])
            except ValueError:
                pass
            if not pro_add_is_here:
                namepath_hdf5 = all_arg[5]
                name_hdf5 = os.path.basename(namepath_hdf5)
                path_hdf5 = os.path.dirname(namepath_hdf5)
            else:
                name_hdf5 = 'Hydro_RUBAR1D_' + namefile[0].replace('.', '')
                path_hdf5 = path_prj
        if len(all_arg) == 7:
            pro_add_is_here = True
            pro_add = int(all_arg[5])
            namepath_hdf5 = all_arg[6]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)

        try:
            inter = int(all_arg[5])
        except ValueError:
            print('Error: Interpolation type should be 0, 1, 2')
            return

        # load rubar
        rubar.load_rubar1d_and_create_grid(name_hdf5, path_hdf5, name_prj, path_prj, 'RUBAR1D', namefile, pathfile,
                                     inter, manning_data, nb_point_vel, False, pro_add, [], path_hdf5, True)

# ----------------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_LAMMI':

        if not 3 < len(all_arg) < 6:
            print('The function LOAD_LAMMI needs two to three inputs. Call LIST_COMMAND for more '
                  'information.')
            return

        facies_path = all_arg[2]
        transect_path = all_arg[2]
        new_dir = all_arg[3]

        if len(all_arg) == 4:
            name_hdf5 = 'Merge_LAMMI_'
            path_hdf5 = path_prj
        elif len(all_arg) == 5:
            namepath_hdf5 = all_arg[3]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)
        else:
            print('Error: Wrong number of intput')
            return

        lammi.open_lammi_and_create_grid(facies_path, transect_path, path_prj, name_hdf5, name_prj, path_prj, path_hdf5,
                                   new_dir, [], False, 'Transect.txt', 'Facies.txt', True, [], 1, 'LAMMI')
# ----------------------------------------------------------------------------------------
    elif all_arg[1] == 'RUN_ESTIMHAB':
        if not len(all_arg) == 12:
            print('RUN_ESTIMHAB needs 12 inputs. See LIST_COMMAND for more info.')
            return
        # path bio
        path_bio2 = os.path.join(path_bio, 'estimhab')
        # input
        try:
            q = [float(all_arg[2]), float(all_arg[3])]
            w = [float(all_arg[4]), float(all_arg[5])]
            h = [float(all_arg[6]), float(all_arg[7])]
            q50 = float(all_arg[8])
            qrange  =[float(all_arg[9]), float(all_arg[10])]
            sub = float(all_arg[11])
        except ValueError:
            print('Error; Estimhab needs float as input')
            return

        # fish
        all_file = glob.glob(os.path.join(path_bio2, r'*.xml'))
        for i in range(0, len(all_file)):
            all_file[i] = os.path.basename(all_file[i])
        fish_list = all_file

        # short check
        if q[0] == q[1]:
            print('Error: two different discharge are needed for estimhab')
            return
        if qrange[0] >= qrange[1]:
            print('Error: A range of discharge is necessary')
            print(qrange)
            return
        if not fish_list:
            print('Error: no fish found for estimhab')
            return
        estimhab.estimhab(q, w, h, q50, qrange, sub, path_bio2, fish_list, path_prj, True, {}, path_prj)
        # plt.show()  # should we let it? It stops the function butit shows the results
    # --------------------------------------------------------------------------------------
    elif all_arg[1] == 'RUN_STATHAB':
        if not 2 < len(all_arg) < 5:
            print('RUN_STATHAB needs one or two arguments: the path to the folder containing the input file and the '
                  'river type.')
            return

        path_files = all_arg[2]
        if not os.path.isdir(path_files):
            print('Folder not found for Stathab.')
            return

        # river type
        if len(all_arg) == 3:
            riv_int = 0
        else:
            try:
                riv_int = int(all_arg[3])
            except ValueError:
                print('Error: The river type should be an int between 0 and 2.')
                return
            if riv_int > 2 or riv_int < 0:
                print('Error: The river type should be an int between 0 and 2 (1).')
                return

        # check taht the needed file are there for temperate and tropical rivers
        if riv_int == 0:
            end_file_reach = ['deb.txt', 'qhw.txt', 'gra.txt', 'dis.txt']
            name_file_allreach = ['bornh.txt', 'bornv.txt', 'borng.txt', 'Pref.txt']

            # check than the files are there
            found_reach = 0
            found_all_reach = 0
            for file in os.listdir(path_files):
                file = file.lower()
                endfile = file[-7:]
                if endfile in end_file_reach:
                    found_reach += 1
                if file in name_file_allreach:
                    found_all_reach += 1
            if not 2 < found_all_reach < 5:
                print('The files bornh.txt or bornv.txt or borng.txt could not be found.')
                return
            if found_reach % 4 != 0:
                print('The files deb.txt or qhw.txt or gra.txt or dis.txt could not be found.')
                return

        else:
            end_file_reach = ['deb.csv', 'qhw.csv', 'ii.csv']
            name_file_allreach = []

            # check than the files are there
            found_reach = 0
            found_all_reach = 0
            for file in os.listdir(path_files):
                file = file.lower()
                endfile = file[-7:]
                if endfile in end_file_reach:
                    found_reach += 1
                endfile = file[-6:]
                if endfile in end_file_reach:
                    found_reach += 1
            if found_reach % 3 != 0:
                print('The files deb.csv or qhw.csv or ii.csv could not be found.')
                return

        # load the txt data
        path_bio2 = os.path.join(path_bio, 'stathab')
        mystathab = stathab_c.Stathab(name_prj,path_prj)
        mystathab.load_stathab_from_txt('listriv', end_file_reach, name_file_allreach, path_files)
        mystathab.path_im = path_prj

        # get fish name and run stathab
        if riv_int == 0:
            [mystathab.fish_chosen, coeff_all] = stathab_c.load_pref('Pref_latin.txt', path_bio2)
            mystathab.stathab_calc(path_bio2)
            fig_opt = output_fig_GUI.create_default_figoption()
            fig_opt['erase_id'] = 'True'
            mystathab.fig_opt = fig_opt
            mystathab.savetxt_stathab()
            mystathab.savefig_stahab()
        elif riv_int == 1:
            name_fish = []
            filenames = load_hdf5.get_all_filename(path_bio2, '.csv')
            for f in filenames:
                if 'uni' in f and f[-7:-4] not in name_fish:
                    name_fish.append(f[-7:-4])
            mystathab.fish_chosen = name_fish
            mystathab.riverint =1
            mystathab.stathab_trop_univ(path_bio2, True)
            mystathab.savetxt_stathab()
            mystathab.savefig_stahab(False)
        elif riv_int == 2:
            name_fish = []
            filenames = load_hdf5.get_all_filename(path_bio2, '.csv')
            for f in filenames:
                if 'biv' in f:
                    name_fish.append(f[-7:-4])
            mystathab.fish_chosen = name_fish
            mystathab.riverint = 2
            mystathab.stathab_trop_biv(path_bio2)
            mystathab.savetxt_stathab()
            mystathab.savefig_stahab(False)

        plt.show()

    # -----------------------------------------------------------------------------------
    elif all_arg[1] == 'RUN_FSTRESS':

        if not 2 < len(all_arg) < 5:
            print('RUN_FSTRESS needs between one and two inputs. See LIST_COMMAND for more information.')
            return

        path_fstress = all_arg[2]
        if len(all_arg) == 3:
            path_hdf5 = path_prj
        else:
            path_hdf5 = all_arg[3]
        # do not change the name from this file which should be in the biology folder.
        name_bio = 'pref_fstress.txt'

        # get the data from txt file
        [riv_name, qhw, qrange] = load_fstress_text(path_fstress)

        if qhw == [-99]:
            return

        # get the preferences curve, all invertebrate are selected by default
        [pref_inver, inv_name] = fstress.read_pref(path_bio, name_bio)

        # save input data in hdf5
        fstress.save_fstress(path_hdf5, path_prj, name_prj, name_bio, path_bio, riv_name, qhw, qrange, inv_name)

        # run fstress
        [vh_all, qmod_all, inv_name] = fstress.run_fstress(qhw, qrange, riv_name, inv_name, pref_inver, inv_name,
                                                           name_prj, path_prj)

        # write output in txt
        # no timestamp
        fstress.write_txt(qmod_all, vh_all, inv_name, path_prj, riv_name, False)

        # plot output in txt
        fstress.figure_fstress(qmod_all, vh_all, inv_name, path_prj, riv_name)
        #plt.show()

    # --------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_SUB_SHP':

        if not 3 < len(all_arg) < 6:
            print('LOAD_SUB_SHP needs between two and three inputs. See LIST_COMMAND for more information.')
            return

        filename = os.path.basename(all_arg[2])
        if not path_input:
            path = os.path.dirname(all_arg[2])
        else:
            path = path_input
        code_type = all_arg[3]

        dominant_case = -1
        if len(all_arg) == 6:
            try:
                dominant_case = int(all_arg[5])
            except ValueError:
                print(' the dominant_case argument should -1 or 1 (1)')
                return
        if dominant_case ==1 or dominant_case == -1:
            pass
        else:
            print(' the dominant_case argument should -1 or 1 (1)')
            return

        [xy, ikle, sub_dom, sub_pg, blob] = substrate.load_sub_shp(filename, path, code_type, dominant_case)
        if ikle == [-99]:
            return
        load_hdf5.save_hdf5_sub(path_prj, path_prj, name_prj, sub_pg, sub_dom, ikle, xy, '', False, 'SUBSTRATE')

        # --------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_SUB_TXT':

        if not 3 < len(all_arg) < 6:
            print('LOAD_SUB_TXT needs between two and three inputs. See LIST_COMMAND for more information.')
            return

        filename = os.path.basename(all_arg[2])
        if not path_input:
            path = os.path.dirname(all_arg[2])
        else:
            path = path_input
        code_type = all_arg[3]

        [xy, ikle, sub_dom2, sub_pg2, x, y, blob, blob] = substrate.load_sub_txt(filename, path, code_type)
        if ikle == [-99]:
            return
        load_hdf5.save_hdf5_sub(path_prj, path_prj, name_prj, sub_pg2, sub_dom2, ikle, xy, '', False, 'SUBSTRATE')

    # ----------------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_SUB_CONST':
        if not 2 < len(all_arg) < 5:
            print('LOAD_SUB_CONST needs one input or two inputs. See LIST_COMMAND for more information. ')
            return
        try:
            sub_val = int(all_arg[2])
        except ValueError:
            print('The substrate value should be a number.')
            return

        if sub_val > 8 or sub_val < 0:
            print('The substrate value should be in the cemagref code.')
            return

        if sub_val == 0:
            for i in range(0, 8):
                if len(all_arg) == 4:
                    namepath_hdf5 = all_arg[3]
                    name_hdf5 = os.path.basename(namepath_hdf5) + str(i+1)
                    path_hdf5 = os.path.dirname(namepath_hdf5)
                else:
                    name_hdf5 = 'Sub_CONST_' + str(i+1)
                    path_hdf5 = path_prj

                load_hdf5.save_hdf5_sub(path_hdf5, path_prj, name_prj, i+1, sub_val, [], [], name_hdf5, True,
                                        'SUBSTRATE')
        else:
            if len(all_arg) == 4:
                namepath_hdf5 = all_arg[3]
                name_hdf5 = os.path.basename(namepath_hdf5)
                path_hdf5 = os.path.dirname(namepath_hdf5)
            else:
                name_hdf5 = 'Sub_CONST_' + str(sub_val)
                path_hdf5 = path_prj

            load_hdf5.save_hdf5_sub(path_hdf5, path_prj, name_prj, sub_val, sub_val, [], [], name_hdf5, True, 'SUBSTRATE')

    # ----------------------------------------------------------------
    elif all_arg[1] == 'MERGE_GRID_SUB':

        if not 4 < len(all_arg) < 7:
            print('MERGE_GRID_SUB needs between three and four inputs. See LIST_COMMAND for more information.')
            return

        if not option_restart:
            hdf5_name_hyd = os.path.basename(all_arg[2])
            hdf5_name_sub = os.path.basename(all_arg[3])
            path_hdf5_in = os.path.dirname(hdf5_name_hyd)
            path_hdf5_in2 = os.path.dirname(hdf5_name_sub)
        else:
            # if we are in restart, we need to find the name of the new hdf5 files
            # it should be the name name than before but with a new time stamp
            hdf5_name_hyd_orr = os.path.basename(all_arg[2])
            hdf5_name_sub_orr = os.path.basename(all_arg[3])
            path_hdf5_in = path_prj
            path_hdf5_in2 = path_prj
            # get all file in projet folder
            if os.path.isdir(path_prj):
                filenames = load_hdf5.get_all_filename(path_prj, '.h5')
            else:
                print('the input directory does not exist.')
                return
            # check if there is similar files
            hdf5_name_hyd = hdf5_name_hyd_orr

            for f in filenames:
                if hdf5_name_hyd_orr[:-3] in f and 'MERGE' not in f:
                    hdf5_name_hyd = f

            hdf5_name_sub = hdf5_name_sub_orr
            found = False

            for f in filenames:
                if hdf5_name_sub_orr[:-25] in f:
                    hdf5_name_sub = f
                    found = True
                if not found and 'Substrate_VAR' in f:
                    hdf5_name_sub = f

        if 'Hydro' in hdf5_name_sub[:5]:
            print('Warning: Hydro cannot be used at the start of the name of a subtrate file.'
                  ' The file was ignored.')
            return
        if 'Sub' == hdf5_name_hyd[:3]:
            print('Warning: Sub cannot be used at the start of the name of an hydrological file. '
                  'The file was ignored.')
            return

        if path_hdf5_in != path_hdf5_in2:
            print('Error: hydro and sub hdf5 should be in the same folder.')
            return

        try:
            default_data = int(all_arg[4])
        except ValueError:
            print('Default data should be an int between 1 and 8 (1).')
            return
        if not 0<default_data<9:
            print('Default data should be an int between 1 and 8 (2).')
            return

        # hdf5
        if len(all_arg) == 6:
            namepath_hdf5 = all_arg[5]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)
        else:
            name_hdf5 = 'MERGE_' + hdf5_name_hyd
            path_hdf5 = path_prj

        # in two function to be able to control the name
        [ikle_both, point_all_both, sub_pg_all_both, sub_dom_all_both, vel_all_both, height_all_both] = \
            mesh_grid2.merge_grid_hydro_sub(hdf5_name_hyd, hdf5_name_sub, path_hdf5, default_data, path_prj)

        if ikle_both == [-99]:
            print('Error: data not merged.')
            return

        load_hdf5.save_hdf5(name_hdf5, name_prj, path_prj, 'SUBSTRATE', 2, path_hdf5, ikle_both,
                             point_all_both, [], vel_all_both, height_all_both, [], [], [], [], True, sub_pg_all_both,
                            sub_dom_all_both, save_option=erase_id)

        # create shpafile to control intput
        load_hdf5.create_shapfile_hydro(name_hdf5, path_hdf5, path_prj, True, erase_id)

    # --------------------------------------------------------------------------------
    elif all_arg[1] == 'MERGE_GRID_RAND_SUB':
        # this merge an hydro hdf5 with a random substrate

        if not 2 < len(all_arg) < 5:
            print('MERGE_GRID_RAND_SUB needs between one and two inputs.')
            return

        # name of the hydrological hdf5
        hdf5_name_hyd = all_arg[2]

        if option_restart:
            print('Warning: Restart is not supported with this command. Please check the filename for correctness.\n')
            print(hdf5_name_hyd)

        # sometimes we re-run a folder with old substrate hdf5 files in it, we do not want to test them in this case
        if 'Substrate_VAR' in hdf5_name_hyd:
            print('Warning: This function cannot be run on a hdf5 substrate file')
            return

        default_data = 1.0

        # create a random substrate in a shp form
        h5name = os.path.basename(hdf5_name_hyd)
        path_h5 = os.path.dirname(hdf5_name_hyd)
        substrate.create_dummy_substrate_from_hydro(h5name, path_h5, 'random_sub', 'Const_cemagref', 0, 100, path_prj)

        # save it in hdf5 form
        filename_shp = 'random_sub.shp'
        [xy, ikle, sub_dom, sub_pg, blob] = substrate.load_sub_shp(filename_shp, path_prj, 'Cemagref', -1)
        if ikle == [-99]:
            return

        # path_im2 = r'C:\Users\diane.von-gunten\HABBY\output_cmd\result_cmd2'
        # substrate.fig_substrate(xy, ikle, sub_pg, sub_dom, path_im2)

        hdf5_name_sub = load_hdf5.save_hdf5_sub(path_prj, path_prj, name_prj, sub_pg, sub_dom, ikle, xy,
                                                '', False, 'SUBSTRATE', True)

        # delete the random shapefile (so we can create a new one without problem)
        for f in os.listdir(path_prj):
            if f[:9] == 'random_sub':
                os.remove(os.path.join(path_prj,f))

        # new merged hdf5 name
        if len(all_arg) == 4:
            namepath_hdf5 = all_arg[3]
            name_hdf5 = os.path.basename(namepath_hdf5)
            path_hdf5 = os.path.dirname(namepath_hdf5)
        else:
            name_hdf5 = 'MERGE_' + h5name
            path_hdf5 = path_prj

        # merge data
        [ikle_both, point_all_both, sub_pg_all_both, sub_dom_all_both, vel_all_both, height_all_both] = \
            mesh_grid2.merge_grid_hydro_sub(hdf5_name_hyd, hdf5_name_sub, path_hdf5, default_data, path_prj)
        if ikle_both == [-99]:
            print('Error: data not merged.')
            return

        # plot last time step
        if len(hdf5_name_hyd) > 33:
            mesh_grid2.fig_merge_grid(point_all_both[-1], ikle_both[-1], path_prj, h5name[6:-26])
        else:
            mesh_grid2.fig_merge_grid(point_all_both[-1], ikle_both[-1], path_prj, h5name)

        # save it
        load_hdf5.save_hdf5(name_hdf5, name_prj, path_prj, 'SUBSTRATE', 2, path_hdf5, ikle_both,
                            point_all_both, [], vel_all_both, height_all_both, [], [], [], [], True, sub_pg_all_both,
                            sub_dom_all_both)

        # create shapefile to test input
        load_hdf5.create_shapfile_hydro(name_hdf5, path_hdf5, path_prj, True, erase_id)

    # --------------------------------------------------------------------------------------------------------

    elif all_arg[1] == 'LOAD_HYDRO_HDF5':
        if len(all_arg) != 3:
            print('LOAD_HYDRO_HDF5 needs one input (the name of the hdf5 file).')
            return

        if not input_file:
            hdf5_name_hyd = all_arg[2]
        else:
            name_hyd = os.path.basename(all_arg[2])
            hdf5_name_hyd = os.path.join(path_input, name_hyd)
        [ikle_all_t, point_all, inter_vel_all, inter_height_all] = load_hdf5.load_hdf5_hyd(hdf5_name_hyd, path_prj)

    # ---------------------------------------------------------------------------------------------
    elif all_arg[1] == 'LOAD_SUB_HDF5':
        if len(all_arg) != 3:
            print('LOAD_sub_HDF5 needs one input (the name of the hdf5 file).')
            return

        if not input_file:
            hdf5_name_sub = all_arg[2]
        else:
            name_sub = os.path.basename(all_arg[2])
            hdf5_name_sub = os.path.join(path_input, name_sub)

        [ikle_sub, point_all_sub, data_sub] = load_hdf5.load_hdf5_sub(hdf5_name_sub, path_prj)

    # --------------------------------------------------------------------------------
    elif all_arg[1] == 'RUN_HABITAT':
        if not 4 < len(all_arg) < 8:
            print('RUN_HAB_COARSE needs between four and five inputs. See LIST_COMMAND for more information.')
            return

        # merge hdf5 (with hydro and subtrate data)
        if not option_restart:
            merge_path_name = all_arg[2]
            merge_name = os.path.basename(merge_path_name)
            path_merge = os.path.dirname(merge_path_name)
        else:
            path_merge = path_prj
            hdf5_name_merge_orr = os.path.basename(all_arg[2])
            # get all file in projet folder
            if os.path.isdir(path_input):
                filenames = load_hdf5.get_all_filename(path_prj, '.h5')
            else:
                print('the input directory does not exist.')
                return
            # check if there is similar files
            merge_name = hdf5_name_merge_orr
            for f in filenames:
                if hdf5_name_merge_orr[:-3] in f:
                    merge_name = f

        # the xml preference files
        bio_names = all_arg[3]
        bio_names = bio_names.split(',')
        for i in range(0, len(bio_names)):  # in case there is spaces
            bio_names[i] = bio_names[i].strip()

        # create name_fish (the name of fish and stage to be calculated)
        # addapt bionames and stage
        stage_chosen = all_arg[4]
        name_fish = []
        stage2 = []
        bio_name2 = []
        [latin_name, stages_all] = bio_info.get_stage(bio_names, path_bio)
        latin_name = list(set(latin_name))
        if stage_chosen == 'all':
            for l in range(0, len(latin_name)):
                for s in stages_all[l]:
                    if len(latin_name[l]) > 10:
                        name_fish.extend([latin_name[l][:10]])
                    else:
                        name_fish.extend([latin_name[l]])
                    stage2.extend([s])
                    bio_name2.extend([bio_names[l]])
        else:
            stage_chosen = stage_chosen.split(',')
            for l in range(0, len(latin_name)):
                for s in stages_all[l]:
                    for sc in stage_chosen:
                        if s in sc:
                            if len(latin_name[l]) > 5:
                                name_fish.extend([latin_name[l][:5]])
                            else:
                                name_fish.extend([latin_name[l]])
                            stage2.extend([s])
                            bio_name2.extend([bio_names[l]])
        stages = stage2
        bio_names = bio_name2

        try:
            run_choice = int(all_arg[5])
        except ValueError:
            print('Error: the choice of run should be an int between 0, 1,2 (usually 0 is used)')
            return

        fig_opt = output_fig_GUI.create_default_figoption()
        fig_opt['text_output'] = 'True'
        fig_opt['shape_output'] = 'True'
        fig_opt['paraview'] = 'True'
        fig_opt['erase_id'] = 'True'

        # run calculation
        # we calculate hab on all the stage in xml preference files
        calcul_hab.calc_hab_and_output(merge_name, path_merge, bio_names, stages, name_fish, name_fish, run_choice,
                                       path_bio, path_prj, path_prj, path_prj, path_prj, [], True, fig_opt)

    # --------------------------------------------------------------------------------------
    elif all_arg[1] == 'CREATE_RAND_SUB':

        if not 2 < len(all_arg) < 5:
            print('CREATE_RAND_SUB needs one or two inputs. See LIST_COMMAND for more information.')
            return
        pathname_h5 = all_arg[2]
        h5name = os.path.basename(pathname_h5)
        path_h5 = os.path.dirname(pathname_h5)

        if len(all_arg) == 4:
            new_name = all_arg[3]
        else:
            new_name = 'rand_sub_' + h5name[:-3]

        substrate.create_dummy_substrate_from_hydro(h5name, path_h5, new_name, 'Cemagref', 0, 300, path_prj)

    # ------------------------------------------------------------------------
    elif all_arg[1] == 'HYDRO_CHRONIC':
        if not len(all_arg) == 6:
            print('HYDRO_CHRONIC needs four inputs. See LIST_COMMAND for more information.')
            return

        merge_files = all_arg[2]
        merge_files = merge_files.split(',')

        path_merges = []
        for m in merge_files:
            path_merges.append(path_prj)

        discharge_in_str = all_arg[3].split(',')
        try:
            discharge_in = list(map(float, discharge_in_str))
        except ValueError:
            print('Error: Discharge input should be a list of float separated by a comma.')
            return
        discharge_out_str = all_arg[4].split(',')
        try:
            discharge_out = list(map(float, discharge_out_str))
        except ValueError:
            print('Error: Discharge output should be a list of float separated by a comma.')
            return

        try:
            minh = float(all_arg[5])
        except ValueError:
            print('Error: Minimum water height should be a float')
            return

        hydraulic_chronic.chronic_hydro(merge_files, path_merges, discharge_in, discharge_out, name_prj, path_prj, minh)

    # ---------------------------------------------------------------------------
    elif all_arg[1] == 'ADD_HYDRO_HDF5':
        if len(all_arg) < 4:
            print('ADD_HYDRO_HDF5 needs at least two arguments. See LIST_COMMAND for more information.')
            return
        filepath1 = ''
        new_name=''
        for i in range(2, len(all_arg)-1):
            if i == 2:
                filepath1 = all_arg[2]
            else:
                old_name = new_name
            filepath2 = all_arg[i+1]
            if not os.path.isfile(filepath1):
                print('Error: The first hdf5 file was not found')
                return
            if not os.path.isfile(filepath2):
                print('Error: The second hdf5 file was not found')
                return
            path1 = os.path.dirname(filepath1)
            path2 = os.path.dirname(filepath2)
            hdf51 = os.path.basename(filepath1)
            hdf52 = os.path.basename(filepath2)

            model_type = 'Imported_hydro'
            new_name = load_hdf5.addition_hdf5(path1, hdf51, path2, hdf52, name_prj, path_prj, model_type, path_prj,
                                               False, True, True, 'ADD_HYDRO_CMD_LAST_' + hdf52[:-3])
            filepath1 = os.path.join(path_prj,new_name + '.h5')
            if 2< i < len(all_arg)-1:
                try:
                    os.remove(os.path.join(path_prj,old_name + '.h5'))
                except FileNotFoundError:
                    print('Error: File not found ' + os.path.join(path_prj,old_name + '.h5') )
                    pass
        # ---------------------------------------------------------------------------
    elif all_arg[1] == 'ADD_MERGE_HDF5':
        if len(all_arg) < 4:
            print('ADD_MERGE_HDF5 needs at least two arguments. See LIST_COMMAND for more information.')
            return
        filepath1 = ''
        new_name = ''
        for i in range(2, len(all_arg) - 1):
            if i == 2:
                filepath1 = all_arg[2]
            else:
                old_name = new_name
            filepath2 = all_arg[i + 1]
            if not os.path.isfile(filepath1):
                print('Error: The first hdf5 file was not found')
                return
            if not os.path.isfile(filepath2):
                print('Error: The second hdf5 file was not found')
                return
            path1 = os.path.dirname(filepath1)
            path2 = os.path.dirname(filepath2)
            hdf51 = os.path.basename(filepath1)
            hdf52 = os.path.basename(filepath2)

            model_type = 'Imported_hydro'
            new_name = load_hdf5.addition_hdf5(path1, hdf51, path2, hdf52, name_prj, path_prj, model_type, path_prj,
                                               True, True, True, 'ADD_MERGE_CMD_LAST_' + hdf52[:-3])
            filepath1 = os.path.join(path_prj, new_name + '.h5')
            if 2 < i < len(all_arg) - 1:
                if old_name != new_name:
                    try:
                        os.remove(os.path.join(path_prj, old_name + '.h5'))
                    except FileNotFoundError:
                        print('Error: File not found ' + os.path.join(path_prj, old_name + '.h5'))
                        pass

    # ----------------------------------------------------------------------------
    elif all_arg[1] == 'COMPARE_TEST':
        if len(all_arg) != 4:
            print('COMPARE_TEST needs two arguments, which are the two paths to the folders to be compared.')
            return

        # get folder name
        folder1 = all_arg[2]
        folder2 = all_arg[3]
        if not os.path.isdir(folder1):
            print('Error: the first folder is not found')
            return
        if not os.path.isdir(folder2):
            print('Error: the second folder is not found')
            return

        # get the names of the files in the folder with the expected files
        filenames_exp = load_hdf5.get_all_filename(folder1, '.txt')

        # check that the expected files exists and have the same content in the folder with the results files
        num_wrong = 0
        for f in filenames_exp:
            # check that file exists
            new_file = os.path.join(folder2, f)
            if not os.path.isfile(new_file):
                print('One file was not created by habby during testing. name of the file: ' + os.path.basename(f))
                num_wrong +=1
            else:
                # check if identical
                if filecmp.cmp(new_file, os.path.join(folder1, f), shallow=False):
                    pass
                else:
                    num_wrong +=1
                    print("One file created by habby during testing was not identical to reference file " +
                          os.path.basename(f))

        # result
        if num_wrong == 0:
            print('TEST ALL GOOD!')
        else:
            print('PROBLEMS WERE FOUND ON ' + str(num_wrong) + ' OUT OF ' + str(len(filenames_exp)) + ' FILES.')
        print('-----------------END TEST -------------------------')

    # ---------------------------------------------------------------------------
    else:
        print('Command not recognized. Try LIST_COMMAND to see available commands.')


def habby_restart(file_comm,name_prj, path_prj, path_bio):
    """
    This function reads a list of command from a text file called file_comm. It then calls all_command one each line
    which does contain the symbol ":" . If the lines contains the symbol ":", it considered as an input.
    Careful, the intput should be in order!!!! The info on the left and sight of the symbol ":" are just there so
    an human can read them more easily. Space does not matters here. We try to write the restart file created
    automatically by HABBY in a "nice" layout, but it just to  read it more easily.

    :param file_comm: a string wehich gives the name of the restart file (with the path)
    :param name_prj: the name of the project, created by default by the main()
    :param path_prj: the path to the project created by default bu the main()
    :param path_bio: the path to the project

    """

    if not os.path.isfile(file_comm):
        print('Error: File for restart was not found. Check the name and path. \n')
        return

    # read file with all command
    with open(file_comm, 'rt') as f:
        all_data_restart = f.read()

    all_data_restart = all_data_restart.split('\n')

    if len(all_data_restart) < 1:
        print('Warning: No command found in the restart file')
        return

    l = 0
    a = time.time()
    for c in all_data_restart:
        if ":" not in c:
            print('-------------------------------------------------------------------')
            print(c)
            c = c.strip()
            if len(c) < 1: # empty line
                pass
            elif c[0] == '#': # comment
                pass
            elif c == 'NAME_PROJECT': # manage project name
                arg1 = all_data_restart[l+1].split(':', 1)
                arg2 = all_data_restart[l+2].split(':', 1)
                if len(arg1) > 0 and len(arg2) > 0:
                    arg2[1] = arg2[1].strip()
                    print(arg2[1])
                    if os.path.isdir(arg2[1]):
                        path_prj = os.path.join(arg2[1], 'restart')
                        name_prj = arg1[1].strip()
                        if not os.path.isdir(path_prj):
                            os.mkdir(path_prj)
                        if not os.path.isfile(os.path.join(path_prj, name_prj + '.xml')):
                            filename_empty = os.path.abspath('src_GUI/empty_proj.xml')
                            copyfile(filename_empty, os.path.join(path_prj, name_prj + '.xml'))

                    else:
                        print('Error: the project folder is not found.\n')
                    print(os.path.join(path_prj, name_prj))
            elif c[:3] == 'ALL':  # all command together
                all_arg_c = ['habby_cmd.py',c[3:].strip()]
                lc = l + 1
                while len(all_data_restart) > lc and ':' in all_data_restart[lc]:  # read argument
                    arg1 = all_data_restart[lc].split(':', 1)
                    arg1 = arg1
                    if len(arg1) > 0:
                        all_arg_c.append(arg1[1].strip())
                    lc += 1
                habby_on_all(all_arg_c, name_prj, path_prj, path_bio)
            else: # command
                all_arg_c = ['habby_cmd.py',c.strip()]
                lc = l+1
                while len(all_data_restart) > lc and ':' in all_data_restart[lc]:  # read argument
                    arg1 = all_data_restart[lc].split(':',1)
                    arg1 = arg1
                    if len(arg1) > 0:
                        all_arg_c.append(arg1[1].strip())
                    lc += 1
                all_command(all_arg_c, name_prj, path_prj, path_bio, True)
                plt.close()
            print('DONE')
            print('-------------------------------------------------------------------')
        l +=1
    b = time.time()
    print(str(l) + ' commands executed in ' + str(b-a)+'sec')


def habby_on_all(all_arg, name_prj, path_prj, path_bio, option_restart=False):
    """
    This function is used to execute a command from habby_cmd on all files in a folder. The form of the command should
    be something like "habby_cmd ALL COMMAND path_to_file/\*.ext arg2 ag3" with the arguments adated to the specific
    command.

    In other words, the command should be the usual command with the keyword ALL before and with the name of
    the input files remplace by \*.ext . where ext is the extension of the files.
    It is better to not add an output name. Indeed default name for output includes the input file name, which
    is practical if different files are given as input. If the default
    is overided, the same name will be applied, only the time stamps will be different. To be sure to not overwrite a
    file, this function waits one second between each command. Only the input argument should containts the string '\*'.
    Otherwise, other commands would be treated as input files.

    If there is more than one type of input, it is important that the name of the file are the same (or at least
    that there are in the same alphabetical order). If the variable # is used instead of \*, the function will be
    applied to all second file one by one. So if we have two substrate file and two hydro file, name with \* will result
    in two merged files while # will result in four merge file.

    If more than one extension is possible (example g01, g02, g03, etc. in hec-ras), remplace the changing part of the
    extension with the symbol \* (so path_to_folder/\*.g0\* arg1 argn). If the name of the file changed in the extension
    as in RUBAR (where the file have the name PROFIL.file), just change for PROFIL.\* or something similar. Generally
    the matching is done using the function glob, so the shell-type wildcard can be used.

    As there are a lot of hdf5 intput, one should be careful to avoid mixing between the different type of hdf5 files.
    For example, it is better to write 'MERGE\*.h5' as just '\*.h5' if the folder contains hydraulic and merge files.

    :param all_arg: the list of argument (sys.argv without the argument ALL so [sys.argv[0], sys.argv[2], sys.argv[n]])
    :param name_prj: the name of the project, created by default by the main()
    :param path_prj: the path to the project created by default bu the main()
    :param path_bio: the path to the project
    :param option_restart: If True the command are coming from a restart log (which have an impact on file name and
           location)
    """

    # if you just read the docstring here, do not forgot that \ is an espcae character for sphinx and * is a special
    # character: \* = *

    # get argv with *. (input name)
    input_folder = []
    place_ind = []
    use_file_one_by_one = False
    for idx, a in enumerate(all_arg):
        if '#' in a:
            a = a.replace('#', '*')
            use_file_one_by_one = True
        if '*' in a:
            input_folder.append(a)
            place_ind.append(idx)
    nb_type = len(place_ind)

    # get all input name
    all_files = []
    dirname = '.'
    for f in input_folder:
        files = glob.glob(f)
        # dirname = os.path.dirname(f)
        # basename = os.path.basename(f)
        # blob,ext = os.path.splitext(basename)
        # if "*" not in ext:
        #     files = load_hdf5.get_all_filename(dirname, ext)
        # else:
        #     pattern = basename
        all_files.append(files)
        if not files:
            print('Warning: No files found for the current ALL command.')

    if len(all_files) == 0:
        print('No file found in the selected folder')
        return

    # if we want to use all files with all file, we will have to correct the file order
    if use_file_one_by_one:
        nb_dim = sum(len(x) for x in all_files[1:])
        all_files_old = deepcopy(all_files)
        if nb_dim >0:
            all_files = [all_files_old[0]*nb_dim]  # fist dim
        else:
            all_files = [all_files_old[0]]  # fist dim
        for i in range(1, len(all_files_old)):
            new_files = [val for val in all_files_old[i] for _ in range(0, len(all_files_old[i-1]))]
            all_files.append(new_files)

    # check that each input type has the same length
    if not all(len(i) == len(all_files[0]) for i in all_files):
        print('The number of each type of input file is not equal. Please check the name of the file below')
        print(all_files)
        return

    # now get through each files
    for i in range(0, len(all_files[0])):
        all_arg_here = all_arg

        # get the file for this command
        # careful files should be in order
        for j in range(0, nb_type):
            all_arg_here[place_ind[j]] = os.path.join(dirname, all_files[j][i])

        # just to check
        print('Execute command ' + all_arg_here[1] + ' on:')
        for i in place_ind:
            print(all_arg_here[i])

        # execute the command
        a = time.time()
        all_command(all_arg_here, name_prj, path_prj, path_bio, option_restart, erase_id=True)
        t = time.time() - a
        print('Command executed in ' + str(t) + ' sec.')
        print('----------------------------------------------------------------------')

        # avoid risk of over-wrting
        time.sleep(1)


def load_manning_txt(filename_path):
    """
    This function loads the manning data in case where manning number is not simply a constant. In this case, the manning
    parameter is given in a .txt file. The manning parameter used by 1D model such as mascaret or Rubar BE to distribute
    velocity along the profiles. The format of the txt file is "p, dist, n" where  p is the profile number (start at zero),
    dist is the distance along the profile in meter and n is the manning value (in SI unit). White space is neglected
    and a line starting with the character # is also neglected.

    There is a very similar function as a method in the class Sub_HydroW() in hydro_GUI.py but it used by the GUI
    and it includes a way to select the file using the GUI and it used a lot of class attribute. So it cannot be used
    by the command line. Changes should be copied in both functions if necessary.

    :param filename_path: the path and the name of the file containing the manning data
    :return: the manning as an array form
    """

    try:
        with open(filename_path, 'rt') as f:
            data = f.read()
    except IOError:
        print('Error: The selected file for manning can not be open.')
        return
    # create manning array (to pass to dist_vitess)
    data = data.split('\n')
    manning = np.zeros((len(data), 3))
    com = 0
    for l in range(0, len(data)):
        data[l] = data[l].strip()
        if len(data[l])>0:
            if data[l][0] != '#':
                data_here = data[l].split(',')
                if len(data_here) == 3:
                    try:
                        manning[l - com, 0] = np.int(data_here[0])
                        manning[l - com, 1] = np.float(data_here[1])
                        manning[l - com, 2] = np.float(data_here[2])
                    except ValueError:
                        print('Error: The manning data could not be converted to float or int.'
                                           ' Format: p,dist,n line by line.')
                        return
                else:
                    print('Error: The manning data was not in the right format.'
                                       ' Format: p,dist,n line by line.')
                    return

            else:
                manning = np.delete(manning, -1, 0)
                com += 1

    return manning


def load_fstress_text(path_fstress):
    """
    This function loads the data for fstress from text files. The data is composed of the name of the rive, the
    discharge range, and the [discharge, height, width]. To read the files, the files listriv.txt is given. Form then,
    the function looks for the other files in the same folder. The other files are rivdeb.txt and rivqwh.txt. If more
    than one river is given in listriv.txt, it load the data for all rivers.

    There is a very similar function as a method in the class FStressW() in fstress_GUI.py but it ised by the GUI
    and it includes a way to select the file using the GUI. Changes should be copied in both functions if necessary.

    :param path_fstress: the path to the listriv.txt function (the other fil should be in the same folder)

    """

    found_file = []
    riv_name = []

    # filename_path
    filename = 'listriv.txt'
    filename_path = os.path.join(path_fstress, filename)

    if not os.path.isfile(filename_path):
        print('Error: listriv.txt could not be found.')
        return [-99],[-99],[-99]

    # get the river name
    with open(filename_path, 'rt') as f:
        for line in f:
            riv_name.append(line.strip())

    # add the file names (deb and qhw.txt)
    for r in riv_name:
        f_found = [None, None]
        # discharge range
        debfilename = r + 'deb.txt'
        if os.path.isfile(os.path.join(path_fstress, debfilename)):
            f_found[1] = debfilename
        elif os.path.isfile(os.path.join(path_fstress, r + 'DEB.TXT')):
            debfilename = r[:-7] + 'DEB.TXT'
            f_found[1] = debfilename
        else:
            f_found[1] = None
        # qhw
        qhwname = r + 'qhw.txt'
        if os.path.isfile(os.path.join(path_fstress, qhwname)):
            f_found[0] = qhwname
        elif os.path.isfile(os.path.join(path_fstress, r + 'QHW.TXT')):
            qhwname = r + 'QHW.TXT'
            f_found[0] = qhwname
        else:
            print('Error: qhw file not found for river ' + r + '.')
            return
        found_file.append(f_found)

    # if not river found
    if len(riv_name) == 0:
        print('Warning: No river found in files')
        return [-99],[-99],[-99]

    # load the data for each river
    qrange = []
    qhw = []
    for ind in range(0, len(found_file)):
        fnames = found_file[ind]

        # discharge range
        if fnames[1] is not None:
            fname_path = os.path.join(path_fstress, fnames[1])
            if os.path.isfile(fname_path):
                with open(fname_path, 'rt') as f:
                    data_deb = f.read()
                data_deb = data_deb.split()
                try:
                    data_deb = list(map(float, data_deb))
                except ValueError:
                    print('Error: Data cannot be converted to float in deb.txt')
                    return
                qmin = min(data_deb)
                qmax = max(data_deb)

                qrange.append([qmin, qmax])
            else:
                print('Error: deb.txt file not found.(1)')
                return [-99], [-99], [-99]
        else:
            print('Error: deb.txt file not found.(2)')
            return [-99], [-99], [-99]

        # qhw
        fname_path = os.path.join(path_fstress, fnames[0])
        if os.path.isfile(fname_path):
            with open(fname_path, 'rt') as f:
                data_qhw = f.read()
            data_qhw = data_qhw.split()
            # useful to pass in float to check taht we have float
            try:
                data_qhw = list(map(float, data_qhw))
            except ValueError:
                print('Error: Data cannot be concerted to float in qhw.txt')
                return [-99], [-99], [-99]
            if len(data_qhw) < 6:
                print('Error: FStress needs at least two discharge measurement.')
                return [-99], [-99], [-99]
            if len(data_qhw)%3 != 0:
                print('Error: One discharge measurement must be composed of three data (q,w, and h).')
                return [-99], [-99], [-99]

            qhw.append([[data_qhw[0], data_qhw[1], data_qhw[2]],[data_qhw[3], data_qhw[4], data_qhw[5]]])
        else:
            print('Error: qwh.txt file not found.(2)')
            return [-99], [-99], [-99]

    return riv_name, qhw, qrange
