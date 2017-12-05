import numpy as np
import sys
import os
from io import StringIO
from src import manage_grid_8
from src_GUI import output_fig_GUI
from src import load_hdf5
from src import rubar

def load_sw2d_and_modify_grid(name_hdf5, geom_sw2d_file, result_sw2d_file, path_geo, path_res, path_im, name_prj,
                              path_prj, model_type, nb_dim, path_hdf5, q=[], print_cmd=False, fig_opt={}):
    """
    This function loads the sw2d file, using the function below. Then, it changes the mesh which has triangle and
    quadrilater toward a triangle mesh and it passes the data from cell-centric data to node data using a linear
    interpolation. Finally it saves the data in one hdf5.

    TODO See if we could improve the interpolation or study its effect in more details.
    :param name_hdf5: the base name of the created hdf5 (string)
    :param geom_sw2d_file: the name of the .geo gile (string)
    :param result_sw2d_file: the name of the result file (string)
    :param path_geo: path to the geo file (string)
    :param path_res: path to the result file which contains the outputs (string)
    :param path_im: the path where to save the figure (string)
    :param name_prj: the name of the project (string)
    :param path_prj: the path of the project (string)
    :param model_type: the name of the model such as Rubar, hec-ras, etc. (string)
    :param nb_dim: the number of dimension (model, 1D, 1,5D, 2D) in a float
    :param path_hdf5: A string which gives the adress to the folder in which to save the hdf5
    :param q: used by the second thread to get the error back to the GUI at the end of the thread
    :param print_cmd: If True will print the error and warning to the cmd. If False, send it to the GUI.
    :param fig_opt: the figure option, used here to get the minimum water height to have a wet node (can be > 0)
    :return: none
    """

    # get minimum water height
    if not fig_opt:
        fig_opt = output_fig_GUI.create_default_figoption()
    minwh = fig_opt['min_height_hyd']

    # find where we should send the error (cmd or GUI)
    if not print_cmd:
        sys.stdout = mystdout = StringIO()

    # create the empy output
    inter_vel_all_t = []
    inter_h_all_t = []
    ikle_all_t = []
    point_all_t = []
    point_c_all_t = []

    # load swd data
    [baryXY, timesteps, height_cell, vel_cell] = read_result_sw2d(result_sw2d_file, path_res)
    if isinstance(baryXY[0], int):
        if baryXY == [-99]:
            print("Error: the SW2D result file could not be loaded.")
            if q:
                sys.stdout = sys.__stdout__
                q.put(mystdout)
                return
            else:
                return
    [noNodElem, listNoNodElem, nodesXYZ] = read_mesh_sw2d(geom_sw2d_file, path_geo)
    if isinstance(noNodElem[0], int):
        if noNodElem == [-99]:
            print("Error: the SW2D geometry file could not be loaded.")
            if q:
                sys.stdout = sys.__stdout__
                q.put(mystdout)
                return
            else:
                return

    # get triangular nodes from quadrilateral
    [ikle_base, coord_c, coord_p, height_cell, vel_cell] = rubar.get_triangular_grid(listNoNodElem, baryXY, \
                                                                                     nodesXYZ[:,:2], height_cell, \
                                                                                     vel_cell)

    # create grid
    # first, the grid for the whole profile (no velocity or height data)
    # because we have a "whole" grid for 1D model before the actual time step
    inter_h_all_t.append([[]])
    inter_vel_all_t.append([[]])
    point_all_t.append([coord_p])
    point_c_all_t.append([coord_c])
    ikle_all_t.append([ikle_base])

    # the grid data for each time step
    warn1 = False
    for t in range(0, len(vel_cell)):
        # get data no the node (and not on the cells) by linear interpolation
        if t == 0:
            [vel_node, height_node, vtx_all, wts_all] = manage_grid_8.pass_grid_cell_to_node_lin([coord_p],
                                                                                                 [coord_c], vel_cell[t],
                                                                                                 height_cell[t], warn1)
        else:
            [vel_node, height_node, vtx_all, wts_all] = manage_grid_8.pass_grid_cell_to_node_lin([coord_p], [coord_c],
                                                                                                 vel_cell[t],
                                                                                                 height_cell[t], warn1,
                                                                                                 vtx_all, wts_all)
        # cut the grid to the water limit
        [ikle, point_all, water_height, velocity] = manage_grid_8.cut_2d_grid(ikle_base, coord_p, height_node[0],
                                                                              vel_node[0], minwh)

        inter_h_all_t.append([water_height])
        inter_vel_all_t.append([velocity])
        point_all_t.append([point_all])
        point_c_all_t.append([[]])
        ikle_all_t.append([ikle])
        warn1 = False

    # save data
    timestep_str = list(map(str, timesteps))
    load_hdf5.save_hdf5(name_hdf5, name_prj, path_prj, model_type, nb_dim, path_hdf5, ikle_all_t, point_all_t,
                        point_c_all_t,
                        inter_vel_all_t, inter_h_all_t, sim_name=timestep_str)

    if not print_cmd:
        sys.stdout = sys.__stdout__
    if q:
        q.put(mystdout)
    else:
        return

def read_mesh_sw2d(geofile, pathfile):
    """
    Reads the binary file of SW2D mesh
    :param geofile: the name of the geometry file (string)
    :param pathfile: the path of the geometry file (string)
    :return: - the number of nodes per element (3 or 4 --> triangle or quadrilateral)
             - the list of nodes for each element
             - x y and z-coordinates of nodes
    """
    failload = [-99], [-99], [-99]
    filename_path = os.path.join(pathfile, geofile)
    try:
        with open(filename_path, 'rb') as f:
            # reading dimensions with Fortran labels
            data = np.fromfile(f, dtype=np.int32, count=5)
            ncel = data[1]
            nint = data[2]
            nnod = data[3]
            # reading info on cells
            noNodElem = np.zeros((ncel, 1), dtype=np.int)
            nnCel = np.zeros((ncel,1), dtype=np.int)
            data = np.fromfile(f, dtype=np.int32, count=1) #label
            for i in range(ncel):
                data = np.fromfile(f, dtype=np.int32, count=3)
                noNodElem[i] = data[0]
                nnCel[i] = data[1]
                data = np.fromfile(f, dtype=np.float, count=4)
            data = np.fromfile(f, dtype=np.int32, count=1) #end label
            # reading connectivity
            ### listNoNodElem = np.zeros([ncel, np.max(noNodElem)], dtype=np.int)
            listNoNodElem = []
            for i in range(int(ncel)):
                data = np.fromfile(f, dtype=np.int32, count=1) #label

                ikle = np.zeros(noNodElem[i], dtype=np.int)

                for j in range(int(noNodElem[i])):
                    ikle[j] = np.fromfile(f, dtype=np.int32, count=1) - 1
                    data = np.fromfile(f, dtype=np.float, count=2)

                listNoNodElem.append(ikle)

                data = np.fromfile(f, dtype=np.int32, count=1) #end label
                data = np.fromfile(f, dtype=np.int32, count=1) #label
                data = np.fromfile(f, dtype=np.int32, count=int(noNodElem[i])) # cint
                data = np.fromfile(f, dtype=np.int32, count=1) #end label
                data = np.fromfile(f, dtype=np.int32, count=1) #label
                data = np.fromfile(f, dtype=np.int32, count=int(nnCel[i])) # ccel
                data = np.fromfile(f, dtype=np.int32, count=1) #end label
                data = np.fromfile(f, dtype=np.int32, count=1) #label
                data = np.fromfile(f, dtype=np.int32, count=int(noNodElem[i])) # cint
                data = np.fromfile(f, dtype=np.int32, count=1) #end label
            # reading info on edges
            data = np.fromfile(f, dtype=np.int32, count=1) #label
            for i in range(nint):
                data = np.fromfile(f, dtype=np.int32, count=4)
                data = np.fromfile(f, dtype=np.float, count=7)
            data = np.fromfile(f, dtype=np.int32, count=1) #end label
            # reading the coordinates of nodes
            nodesXYZ = np.zeros((nnod, 3))
            data = np.fromfile(f, dtype=np.int32, count=1) #label
            for i in range(nnod):
                nodesXYZ[i,] = np.fromfile(f, dtype=np.float, count=3)
                data = np.fromfile(f, dtype=np.int32, count=1)
            data = np.fromfile(f, dtype=np.int32, count=1) #end label
                
    except IOError:
        print('Error: The .geo file does not exist')
        return failload
    f.close()
    return noNodElem, listNoNodElem, nodesXYZ


def read_result_sw2d(resfile, pathfile):
    """
    Reads the binary file of SW2D results
    
    :param resfile: the name of the result file (string)
    :param pathfile: path of the result file (string)
    :return: - barycentric coordinates of each elements
             - time values
             - water depth and velocity values for each time step and element
    """
    failload = [-99], [-99], [-99], [-99]
    filename_path = os.path.join(pathfile, resfile)
    try:
        with open(filename_path, 'rb') as f:
            # reading storage info with Fortran labels
            data = np.fromfile(f, dtype=np.int32, count=18)
            # reading dimensions with Fortran labels
            data = np.fromfile(f, dtype=np.int32, count=4)
            ncel = data[1]
            nint = data[2]
            # reading barycentric coordinates
            ###baryXY = np.zeros((ncel, 2))
            baryXY = []
            cxy = np.zeros(2)
            data = np.fromfile(f, dtype=np.int32, count=1) #label
            for i in range(ncel):
                #baryXY[i,] = np.fromfile(f, dtype=np.float, count=2)
                cxy = np.fromfile(f, dtype=np.float, count=2)
                baryXY.append(cxy)
            data = np.fromfile(f, dtype=np.int32, count=1) #end label
            # reading info on edges
            data = np.fromfile(f, dtype=np.int32, count=1) #label
            for i in range(nint):
                data = np.fromfile(f, dtype=np.int32, count=2)
                data = np.fromfile(f, dtype=np.float, count=6)
            data = np.fromfile(f, dtype=np.int32, count=1) #end label
            # reading results
            times = np.array([]).reshape(0, 1)
            h = np.array([]).reshape(0, ncel)
            v = np.array([]).reshape(0, ncel)
            while True:
                data = np.fromfile(f, dtype=np.int32, count=1) #label
                if data.size < 1:
                    break
                timeval = np.fromfile(f, dtype=np.float, count=1)
                nvar = np.fromfile(f, dtype=np.int32, count=1)
                data = np.fromfile(f, dtype=np.int32, count=1) #end label
                times = np.vstack([times, timeval])
                data = np.fromfile(f, dtype=np.int32, count=1) #label
                result = np.fromfile(f, dtype=np.float, count=ncel)
                data = np.fromfile(f, dtype=np.int32, count=1) #end label
                if nvar == 1:
                    h = np.vstack([h, result])
                elif nvar == 8:
                    v = np.vstack([v, result])
    except IOError:
        print('Error: The .res file does not exist')
        return failload
    f.close()
    return baryXY, np.unique(times), h, v

if __name__ == '__main__':
    # read the mesh of sw2d
    result_sw2d_file = 'a.geo'
    mesh_sw2d = read_mesh_sw2d(result_sw2d_file)
    # read results on the water depth and velocity for all time steps
    result_sw2d_file = 'alex23.res'
    result_sw2d = read_result_sw2d(result_sw2d_file)

    print(result_sw2d)
    
