"""
TODO Can I remove movement classes if I just use degrees of freedom and reference axes?

"""

import logging

from scipy.spatial.distance import euclidean

from .kinematics.transformations import translate, rotate, rigid_transformation
from .kinematics.depricated_kinematics import calculate_static_positions, calculate_independent_positions

from matplotlib import colors as mcolors

logger = logging.getLogger(__name__)

import numpy as np
from typing import Union


class Component:

    def __init__(self,
                 name: str,
                 positions: np.ndarray,
                 radii: np.ndarray,
                 color: str,
                 movement_class: str,
                 reference_axes: str = 'origin',
                 degrees_of_freedom: Union[tuple[str], None] = ('x', 'y', 'z', 'rx', 'ry', 'rz'),
                 ports: Union[None, list[dict]] = None):

        self.name = self._validate_name(name)
        self.positions = self._validate_positions(positions)
        self.radii = self._validate_radii(radii)
        # TODO Remove rotation...
        self.rotation = np.zeros(3)
        self.reference_axes = self._validate_reference_axes(reference_axes)
        self.movement_class = self._validate_movement_class(movement_class)
        self.degrees_of_freedom = self._validate_degrees_of_freedom(degrees_of_freedom)
        self.ports = self._validate_ports(ports)
        self.port_names = []
        self.port_indices = []

        self._valid_colors = {**mcolors.BASE_COLORS, **mcolors.TABLEAU_COLORS, **mcolors.CSS4_COLORS,
                              **mcolors.XKCD_COLORS}

        self.color = self._validate_colors(color)

        if self.ports is not None:
            for port in self.ports:
                self.port_names.append(port['name'])
                self.positions = np.vstack((self.positions, port['origin']))
                self.radii = np.concatenate((self.radii, [port['radius']]))
                self.port_indices.append(len(self.positions) - 1)


    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError('Name must be a string not %s.' % type(name))
        return name

    def port_index(self, port_name: str) -> int:
        if port_name not in self.port_names:
            raise ValueError('Port name %s is not in %s.' % (port_name, self.name))
        return self.port_indices[self.port_names.index(port_name)]

    def port_position(self, port_name: str) -> np.ndarray:
        if port_name not in self.port_names:
            raise ValueError('Port name %s is not in %s.' % (port_name, self.name))
        return self.positions[self.port_indices[self.port_names.index(port_name)]]

    def _validate_positions(self, positions: np.ndarray) -> np.ndarray:

        if positions is None:
            raise ValueError('Positions have not been set for %s.' % self.__repr__())

        if not isinstance(positions, list) and not isinstance(positions, np.ndarray):
            raise ValueError(
                'Positions must be a list or numpy array for %s not %s.' % (self.__repr__(), type(positions)))

        if isinstance(positions, list):
            logger.warning('Positions should be a numpy array for %s.' % self.__repr__())
            positions = np.array(positions)

        if len(positions.shape) == 1:
            logger.warning('Positions are not 2D for %s.' % self.__repr__())
            positions = positions.reshape(-1, 3)

        if positions.shape[1] != 3:
            raise ValueError('Positions must be 3D for %s.' % self.__repr__())

        return positions

    def _validate_radii(self, radii: np.ndarray) -> np.ndarray:

        if radii is None:
            raise ValueError('Radii have not been set for %s.' % self.__repr__())

        if isinstance(radii, float):
            logger.warning('Radii should be a numpy array for %s.' % self.__repr__())
            radii = np.array([radii])

        if isinstance(radii, list):
            logger.warning('Radii should be a numpy array for %s.' % self.__repr__())
            radii = np.array(radii)

        if len(radii.shape) > 1:
            logger.warning('Radii should be 1D for %s.' % self.__repr__())
            radii = radii.reshape(-1)

        if radii.shape[0] != self.positions.shape[0]:
            raise ValueError('There must be 1 radius for each position row for %s.' % self.__repr__())

        return radii

    def _validate_movement_class(self, movement_class):

        if not isinstance(movement_class, str):
            raise TypeError('Movement must be a string for %s.' % self.__repr__())

        valid_movement_classes = ['static', 'independent', 'partially_dependent', 'fully_dependent']
        if movement_class not in valid_movement_classes:
            raise ValueError('Movement class not recognized for %s. Valid movement classes are: %s' %
                             (self.__repr__(), valid_movement_classes))

        return movement_class

    def _validate_reference_axes(self, reference_axes):
        # TODO Ensure that is no reference objects are not specified that movement class isn't dependent
        # TODO Add logic to ensure dynamic fully dependent objects don't reference other dynamic fully dependent objects
        # TODO Update for dictionary and None...
        # if reference_objects is None:
        #
        #     # Quick workaround - include independent since "dependent" is in it...
        #     if 'independent' in self.movement_class:
        #         pass
        #     elif 'dependent' in self.movement_class:
        #         raise ValueError('Reference objects must be specified for dependent movement for %s.' % self.name)
        #     else:
        #         pass
        #
        # elif isinstance(reference_objects, str):
        #     # TODO Add a system-integration test to ensure that only valid reference objects are specified
        #     pass
        #
        # elif isinstance(reference_objects, list):
        #     for reference_object in reference_objects:
        #         if not isinstance(reference_object, str):
        #             raise TypeError('Reference objects must be a string for %s.' % self.name)
        #
        #         # TODO Add a system-integration test to ensure that only valid reference objects are specified
        # else:
        #     raise TypeError('Reference objects must be NoneType, a string or a list for %s.' % self.name)

        return reference_axes

    def _validate_degrees_of_freedom(self, degrees_of_freedom):

        if not isinstance(degrees_of_freedom, tuple) and degrees_of_freedom is not None:
            raise TypeError('Degrees of freedom must be a tuple for %s.' % self.name)

        if degrees_of_freedom is not None:
            for dof in degrees_of_freedom:
                if dof not in ('x', 'y', 'z', 'rx', 'ry', 'rz'):
                    raise ValueError('Invalid DOF specified for %s.' % self.name)

        return degrees_of_freedom

    def _validate_color(self, color):

        if not isinstance(color, str):
            raise ValueError('Color must be a string.')

        if color not in self._valid_colors:
            raise ValueError('Color not recognized. For a list of valid colors inspect the attribute '
                             'self._valid_colors.keys().')

    def _validate_colors(self, colors):

        if colors is None:
            raise ValueError(f'Color has not been set for {self.__repr__()}')

        if isinstance(colors, list):

            if len(colors) == 1:
                self._validate_color(colors)

            if len(colors) > 1:
                for color in colors:
                    self._validate_color(color)

        elif isinstance(colors, str):
            self._validate_color(colors)
        else:
            raise ValueError('Colors must be a list or string.')

        return colors

    def _validate_ports(self, ports):

        if ports is None:
            return ports

        if not isinstance(ports, list):
            raise TypeError('Ports must be a list.')

        # for port in ports:
        #     if not isinstance(port, Port):
        #         raise TypeError('Ports must be a list of Port objects.')

        return ports

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    @property
    def reference_position(self):
        """
        Returns the reference position of the object.

        TODO Replace with a signed distance function that is consistent regardless of the number of spheres used.
        """
        return self.positions[0]

    @property
    def design_vector_dict(self) -> dict:

        """
        Returns a dictionary of the design vector components.

        An object's design vector is encoded as a reference position and rotation. Since objects are rigid bodies,
        all other geometric properties are a function of the reference position and rotation.
        """

        design_vector_dict = {}

        if 'x' in self.degrees_of_freedom:
            design_vector_dict['x'] = self.reference_position[0]
        if 'y' in self.degrees_of_freedom:
            design_vector_dict['y'] = self.reference_position[1]
        if 'z' in self.degrees_of_freedom:
            design_vector_dict['z'] = self.reference_position[2]
        if 'rx' in self.degrees_of_freedom:
            design_vector_dict['rx'] = self.rotation[0]
        if 'ry' in self.degrees_of_freedom:
            design_vector_dict['ry'] = self.rotation[1]
        if 'rz' in self.degrees_of_freedom:
            design_vector_dict['rz'] = self.rotation[2]

        return design_vector_dict

    @property
    def design_vector(self):
        design_vector = np.array(list(self.design_vector_dict.values()))
        return design_vector

    def decompose_design_vector(self, design_vector: np.ndarray) -> dict:
        """
        Takes a 1D design vector and decomposes it into a dictionary of design variables.
        """

        if len(design_vector) != len(self.degrees_of_freedom):
            raise ValueError('The specified design vector must be the same length as the degrees of freedom.')

        design_vector_dict = {}

        for i, dof in enumerate(self.degrees_of_freedom):
            design_vector_dict[dof] = design_vector[i]

        return design_vector_dict

    def calculate_positions(self, design_vector, positions_dict=None):


        # If the object has no degrees of freedom, then return its current position
        if self.degrees_of_freedom is None:
            return {self.__repr__(): self.positions}

        # Extract the design variables from the design vector
        design_vector_dict = self.decompose_design_vector(design_vector)

        if 'x' in self.degrees_of_freedom:
            x = design_vector_dict['x']
        else:
            x = 0

        if 'y' in self.degrees_of_freedom:
            y = design_vector_dict['y']
        else:
            y = 0

        if 'z' in self.degrees_of_freedom:
            z = design_vector_dict['z']
        else:
            z = 0

        if 'rx' in self.degrees_of_freedom:
            rx = design_vector_dict['rx']
        else:
            rx = 0

        if 'ry' in self.degrees_of_freedom:
            ry = design_vector_dict['ry']
        else:
            ry = 0

        if 'rz' in self.degrees_of_freedom:
            rz = design_vector_dict['rz']
        else:
            rz = 0

        # TODO Add reference axes argument
        # Calculate the new positions
        new_positions = rigid_transformation(self.reference_position, self.positions, x, y, z, rx, ry, rz)

        if self.ports is None:
            return {self.__repr__(): new_positions}
        else:

            dict = {}

            # Get non-port positions
            non_port_positions = new_positions[0:self.port_indices[0]]
            dict[self.__repr__()] = non_port_positions

            # Get port positions
            for i, port in enumerate(self.ports):
                port_positions = new_positions[self.port_indices[i]]
                port_name = self.__repr__() + '_' + port['name']
                dict[port_name] = port_positions.reshape(1, 3)

            return dict



    def set_positions(self,
                      positions_dict: dict):
        """
        Update positions of object spheres given a design vector

        :param positions_dict:
        :return:
        """

        self.positions, self.radii = positions_dict[self.__repr__()]


class InterconnectWaypoint(Component):
    def __init__(self,
                 node,
                 radius,
                 color,
                 degrees_of_freedom: Union[tuple[str], None] = ('x', 'y', 'z'),
                 constraints: Union[None, tuple[str]] = None):
        self.name = node
        self.node = node
        self.radius = radius
        self.color = color

        # delete this redundant (used for plotting)
        self.radii = np.array([radius])
        # TODO Sort out None value vs dummy values
        self.positions = np.array([[0., 0., 0.]])  # Initialize a dummy value
        self.movement_class = 'independent'
        self.degrees_of_freedom = degrees_of_freedom
        self.reference_objects = constraints

    # def calculate_positions(self, design_vector, positions_dict):
    #     # TODO Add functionality to accept positions_dict and work for InterconnectSegments
    #
    #     new_positions = self.positions
    #
    #     new_reference_position = design_vector[0:3]
    #     new_positions = translate(new_positions, self.reference_position, new_reference_position)
    #
    #     # TODO Should we
    #     positions_dict[str(self)] = (new_positions, self.radii)
    #
    #     return positions_dict


"""
TODO
Interconnect should be a single object, not subclasses
-represent as bar
-calculate interference as bars
-plot as bars

"""


class InterconnectEdge(Component):
    def __init__(self,
                 name,
                 object_1,
                 object_2,
                 radius,
                 color,
                 port_1=None,
                 port_2=None,
                 degrees_of_freedom: Union[tuple[str], None] = None,
                 constraints: Union[None, tuple[str]] = None):

        self.name = name
        self.object_1 = object_1
        self.port_1   = port_1
        self.object_2 = object_2
        self.port_2   = port_2

        self.radius = radius
        self.color = color

        self.degrees_of_freedom = degrees_of_freedom
        self.reference_objects = constraints

        # # Create edge tuple for NetworkX graphs
        # self.edge = (self.object_1, self.object_2)

        # Placeholder for plot test functionality, random positions
        # self.positions = None
        self.positions = np.empty((0, 3))
        self.radii = None

        self.movement_class = 'fully dependent'

    def calculate_positions(self, _, positions_dict):
        # TODO Remove temp design vector argument
        # TODO revise logic for getting the reference point instead of object's first sphere
        # Address varying number of spheres

        # TODO FIX THIS?
        # Design vector not used
        if isinstance(self.object_1, Component):
            object_1_port_index = self.object_1.port_index(self.port_1)
            pos_1 = positions_dict[self.object_1][0][object_1_port_index]
        else:
            pos_1 = positions_dict[self.object_1][0]

        if isinstance(self.object_2, Component):
            object_2_port_index = self.object_2.port_index(self.port_2)
            pos_2 = positions_dict[self.object_2][0][object_2_port_index]
        else:
            pos_2 = positions_dict[self.object_2][0]

        # Replace with pure-python implementation for Numba
        dist = euclidean(pos_1, pos_2)

        # We don't want zero-length interconnects or interconnect segments--they cause problems!
        num_spheres = 10  # int(dist / (self.radius*1.5))
        # if num_spheres == 0:
        #     num_spheres = 1

        positions = np.linspace(pos_1, pos_2, num_spheres)
        radii = np.repeat(self.radius, num_spheres)

        positions_dict[str(self)] = (positions, radii)

        # TODO Change positions_dict to include kwarg and return addition?
        return positions_dict

    def set_positions(self,
                      positions_dict: dict) -> dict:
        # self.positions, self.radii = positions_dict[self.name]

        # TODO Remove dummy input for design vector
        self.positions = self.calculate_positions([], positions_dict)[str(self)][0]  # index zero for tuple

        # TODO Separate this into a different function?
        self.radii = np.repeat(self.radius, self.positions.shape[0])


class Interconnect(InterconnectWaypoint, InterconnectEdge):
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
                 component_1,
                 component_1_port,
                 component_2,
                 component_2_port,
                 radius,
                 color,
                 number_of_bends):

        self.name = name

        self.component_1 = component_1
        self.component_2 = component_2

        self.component_1_port = component_1_port
        self.component_2_port = component_2_port

        # self.object_1 = self.component_1 + '-' + self.component_1_port + '_port'
        # self.object_2 = self.component_2 + '-' + self.component_2_port + '_port'

        self.radius = radius
        self.color = color

        # self.number_of_bends = number_of_bends

        self.number_of_bends = number_of_bends
        self.number_of_edges = self.number_of_bends + 1

        # Create InterconnectNode objects
        self.nodes, self.node_names = self.create_nodes()
        self.interconnect_nodes = self.nodes[1:-1]  # trims off components 1 and 2

        # Create InterconnectSegment objects
        self.node_pairs = self.create_node_pairs()
        self.segments = self.create_segments()

    def create_nodes(self):
        """
        Consideration: if I include the component nodes then... ?

        TODO replace node names w/ objects!

        :return:
        """
        # TODO Make sure nodes are 2D and not 1D!

        # Create the nodes list and add component 1
        nodes = [self.component_1]
        node_names = [self.component_1]

        # nodes = []
        # node_names = []

        # Add the interconnect nodes
        for i in range(self.number_of_bends):
            # Each node should have unique identifier
            node_name = self.name + '_node_' + str(i)

            interconnect_node = InterconnectWaypoint(node_name, self.radius, self.color)
            nodes.append(interconnect_node)
            node_names.append(node_name)

        # Add component 2
        nodes.append(self.component_2)
        node_names.append(self.component_2)

        return nodes, node_names

    def create_node_pairs(self):

        node_pairs = [(self.node_names[i], self.node_names[i + 1]) for i in range(len(self.node_names) - 1)]

        return node_pairs

    def create_segments(self):

        segments = []

        i = 0
        for object_1, object_2 in self.node_pairs:
            name = self.component_1 + '-' + self.component_2 + '_edge_' + str(i)
            i += 1

            if isinstance(object_1, Component):
                port_1 = self.port_1
            else:
                port_1 = None

            if isinstance(object_2, Component):
                port_2 = self.port_2
            else:
                port_2 = None

            segments.append(InterconnectEdge(name, object_1, object_2, self.radius, self.color,port_1=port_1, port_2=port_2))

        return segments

    # @property
    # def edges(self):
    #     return [segment.edge for segment in self.segments]
