"""
TODO Can I remove movement classes if I just use degrees of freedom and reference axes?

"""


from SPI2py.group_model.component_geometry.finite_sphere_method import read_xyzr_file, generate_rectangular_prisms
from SPI2py.group_model.component_spatial.spatial_transformations import affine_transformation

from matplotlib import colors as mcolors

import torch

from typing import Union, Sequence

import pyvista as pv


class Component:
    """
    TODO Update set position to just set the origin.. positions should be a SDF(?)
    """
    def __init__(self,
                 name: str,
                 color: str = None,
                 degrees_of_freedom: Sequence[str] = ('x', 'y', 'z', 'rx', 'ry', 'rz'),
                 filepath=None,
                 ports: list[dict] = []):

        self.name = name


        self.positions, self.radii = read_xyzr_file(filepath)
        self.rotation = torch.tensor([0, 0, 0], dtype=torch.float64)
        self.scale = torch.tensor([1, 1, 1], dtype=torch.float64)

        self.ports = ports
        self.port_indices = {}

        # TODO Set default design vectors...

        self.degrees_of_freedom = degrees_of_freedom


        self.color = color

        # TODO Make tuple len zero not none
        self.dof = len(self.degrees_of_freedom)

        if self.ports is not None:
            for port in self.ports:
                self.port_indices[port['name']] = len(self.positions - 1)
                self.positions = torch.vstack((self.positions, torch.tensor(port['origin'], dtype=torch.float64)))
                self.radii = torch.cat((self.radii, torch.tensor([port['radius']], dtype=torch.float64)))



    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    @property
    def reference_position(self):
        """
        Returns the reference position of the object.
        """

        x_mean = torch.mean(self.positions[:, 0])
        y_mean = torch.mean(self.positions[:, 1])
        z_mean = torch.mean(self.positions[:, 2])

        return torch.tensor([x_mean, y_mean, z_mean], dtype=torch.float64)

    @property
    def design_vector(self):

        design_vector = []

        if 'x' in self.degrees_of_freedom:
            design_vector.append(self.reference_position[0])
        if 'y' in self.degrees_of_freedom:
            design_vector.append(self.reference_position[1])
        if 'z' in self.degrees_of_freedom:
            design_vector.append(self.reference_position[2])

        if 'rx' in self.degrees_of_freedom:
            design_vector.append(self.rotation[0])
        if 'ry' in self.degrees_of_freedom:
            design_vector.append(self.rotation[1])
        if 'rz' in self.degrees_of_freedom:
            design_vector.append(self.rotation[2])

        if 'sx' in self.degrees_of_freedom:
            design_vector.append(self.scale[0])
        if 'sy' in self.degrees_of_freedom:
            design_vector.append(self.scale[1])
        if 'sz' in self.degrees_of_freedom:
            design_vector.append(self.scale[2])

        return torch.tensor(design_vector, dtype=torch.float64)




    def decompose_design_vector(self, design_vector: torch.tensor) -> dict:
        """
        Takes a 1D design vector and decomposes it into a dictionary of design variables.
        """

        if len(design_vector) != len(self.degrees_of_freedom):
            raise ValueError('The specified design vector must be the same length as the degrees of freedom.')

        design_vector_dict = {}

        for i, dof in enumerate(self.degrees_of_freedom):
            design_vector_dict[dof] = design_vector[i]

        return design_vector_dict

    def assemble_transformation_vectors(self, design_vector_dict):

        translation = torch.zeros((3,1), dtype=torch.float64)
        rotation = torch.zeros((3,1), dtype=torch.float64)
        scale = torch.ones((3,1), dtype=torch.float64)

        if 'x' in self.degrees_of_freedom:
            translation[0] = design_vector_dict['x']
        if 'y' in self.degrees_of_freedom:
            translation[1] = design_vector_dict['y']
        if 'z' in self.degrees_of_freedom:
            translation[2] = design_vector_dict['z']

        if 'rx' in self.degrees_of_freedom:
            rotation[0] = design_vector_dict['rx']
        if 'ry' in self.degrees_of_freedom:
            rotation[1] = design_vector_dict['ry']
        if 'rz' in self.degrees_of_freedom:
            rotation[2] = design_vector_dict['rz']

        if 'sx' in self.degrees_of_freedom:
            scale[0] = design_vector_dict['sx']
        if 'sy' in self.degrees_of_freedom:
            scale[1] = design_vector_dict['sy']
        if 'sz' in self.degrees_of_freedom:
            scale[2] = design_vector_dict['sz']

        return translation, rotation, scale


    def calculate_positions(self, design_vector=None, objects_dict=None, transformation_vectors=None):
        """
        Calculates the positions of the object's spheres.
        """

        if design_vector is not None:
            design_vector_dict = self.decompose_design_vector(design_vector)
            translation, rotation, scaling = self.assemble_transformation_vectors(design_vector_dict)
        else:
            translation, rotation, scaling = transformation_vectors

        new_positions = affine_transformation(self.reference_position.reshape(-1,1), self.positions.T, translation, rotation, scaling).T

        object_dict = {self.__repr__(): {'positions': new_positions, 'radii': self.radii}}

        return object_dict


    def set_positions(self,
                      objects_dict: dict = None,
                      design_vector: list = None,
                      transformation_vectors: list = None):
        """
        Update positions of object spheres given a design vector

        :param objects_dict:
        :param design_vector:
        :return:
        """

        if design_vector is not None:
            objects_dict = self.calculate_positions(design_vector, force_update=True)

        elif transformation_vectors is not None:
            objects_dict = self.calculate_positions(transformation_vectors=transformation_vectors)


        self.positions = objects_dict[self.__repr__()]['positions']
        self.radii     = objects_dict[self.__repr__()]['radii']

    def generate_plot_objects(self):
        objects = []
        colors = []
        for position, radius in zip(self.positions, self.radii):
            objects.append(pv.Sphere(radius=radius, center=position))
            colors.append(self.color)

        return objects, colors


class Interconnect:
    """
    Interconnects are made of one or more non-zero-length segments and connect two components.

    TODO Add a class of components for interconnect dividers (e.g., pipe tee for a three-way split)

    When an interconnect is initialized it does not contain spatial information.

    In the SPI2 class the user specifies which layout generation method to use, and that method tells
    the Interconnect InterconnectNodes what their positions are.

    For now, I will assume that interconnect nodes will start along a straight line between components A
    and B. In the near future they may be included in the layout generation method. The to-do is tracked
    in spatial_configuration.py.

    # placeholder
        component_1 = [i for i in self.components if repr(i) == self.component_1][0]
        component_2 = [i for i in self.components if repr(i) == self.component_2][0]
    """

    def __init__(self,
                 name,
                 component_1_name,
                 component_1_port_index,
                 component_2_name,
                 component_2_port_index,
                 radius,
                 color,
                 number_of_waypoints,
                 degrees_of_freedom):

        self.name = name

        self.component_1_name = component_1_name
        self.component_2_name = component_2_name

        self.component_1_port_index = component_1_port_index
        self.component_2_port_index = component_2_port_index

        self.radius = radius
        self.color = color

        self.number_of_waypoints = number_of_waypoints
        self.segments_per_interconnect = self.number_of_waypoints - 1

        self.degrees_of_freedom = degrees_of_freedom

        self.waypoint_positions = torch.zeros((self.number_of_waypoints, 3), dtype=torch.float64)

        self.dof = 3 * self.number_of_waypoints

        self.spheres_per_segment = 25

        self.positions = torch.empty((self.spheres_per_segment*self.segments_per_interconnect,3), dtype=torch.float64)
        self.radii = torch.empty((self.spheres_per_segment*self.segments_per_interconnect,1), dtype=torch.float64)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    @property
    def design_vector(self):
        return self.waypoint_positions.flatten()

    def calculate_positions(self, design_vector, objects_dict):

        # TODO Make this work with design vectors of not length 3
        # Reshape the design vector to extract xi, yi, and zi positions
        design_vector = torch.tensor(design_vector, dtype=torch.float64)
        design_vector = design_vector.reshape((self.number_of_waypoints, 3))

        object_dict = {}

        pos_1 = objects_dict[self.component_1_name]['positions'][self.component_1_port_index]
        pos_2 = objects_dict[self.component_2_name]['positions'][self.component_2_port_index]

        node_positions = torch.vstack((pos_1, design_vector, pos_2))

        start_arr = node_positions[0:-1]
        stop_arr = node_positions[1:None]

        diff_arr = stop_arr - start_arr
        n = self.spheres_per_segment
        increment = diff_arr / n

        start_arr = start_arr.reshape(-1, 3, 1)
        increment = increment.reshape(-1, 3, 1)
        points = start_arr + increment * torch.arange(n).reshape(1, 1, -1)

        # Reshape back into a 2D array
        points = points.reshape(-1, 3)

        # points = torch.linspace(start_arr, stop_arr, self.spheres_per_segment).reshape(-1, 3)
        radii = self.radius * torch.ones(len(points))

        object_dict[str(self)] = {'type': 'interconnect', 'positions': points, 'radii': radii}

        return object_dict

    def set_positions(self, design_vector, objects_dict):
        objects_dict = {**objects_dict, **self.calculate_positions(design_vector, objects_dict)}
        self.waypoint_positions = torch.tensor(design_vector, dtype=torch.float64).reshape((-1, 3))
        self.positions = objects_dict[str(self)]['positions']
        self.radii = objects_dict[str(self)]['radii']


    def generate_plot_objects(self):
        objects, colors = [], []
        for position, radius in zip(self.positions, self.radii):
            objects.append(pv.Sphere(radius=radius, center=position))
            colors.append(self.color)

        return objects, colors
