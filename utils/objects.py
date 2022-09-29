"""Module...
Docstring

To Do:
-Fill out all the blank functions and write tests for them...
-Look into replacing get/set methods with appropriate decorators...


"""

import numpy as np
import networkx as nx
from itertools import product, combinations
from utils.shape_generator import generate_rectangular_prism, generate_rectangular_prisms
from utils.visualization import plot
from utils.transformations import translate, rotate


class Object:

    # Can I add a component instance counter here? Do I need it?

    def __init__(self, positions, radii, color, name):
        self.positions = positions
        self.radii = radii
        self.color = color
        self.name = name

    @property
    def reference_position(self):
        return self.positions[0]

    @reference_position.setter
    def reference_position(self, new_reference_position):
        self.positions[0] = new_reference_position






class Component(Object):

    def __init__(self, positions, radii, color, node, name):

        super().__init__(positions, radii, color, name)

        self.node = node

        self.rotation = np.array([0,0,0]) # Initialize the rotation attribute

    def get_node(self):
        return self.node

    def get_rotation(self):
        return self.rotation

    def set_rotation(self, new_rotation):
        self.rotation = new_rotation

    def get_design_vector(self):
        pass


class InterconnectNode(Object):
    def __init__(self, node):
        self.node = node

    def get_node(self):
        return self.node



class Interconnect(Object):
    def __init__(self, component_1, component_2, diameter, color):
        self.component_1 = component_1
        self.component_2 = component_2
        self.diameter = diameter
        self.color = color

        # Create edge tuple for NetworkX graphs
        self.edge = (self.component_1, self.component_2)

        # Placeholder for plot test functionality, random positions
        self.positions = np.array([[0, 0, 0]])
        self.radii = np.array([0.5])

    def get_edge(self):
        return self.edge


class Structure(Object):
    def __init__(self, positions, radii, color, name):
        super().__init__(positions, radii, color, name)


class Layout:
    def __init__(self, components, interconnect_nodes, interconnects, structures):
        self.components = components
        self.interconnect_nodes = interconnect_nodes
        self.interconnects = interconnects
        self.structures = structures

        # All objects
        self.objects = components + interconnect_nodes + interconnects + structures

        # All objects with a design vector
        self.design_objects = components + interconnect_nodes

        #
        self.nodes = [design_object.get_node() for design_object in self.design_objects]
        self.edges = [interconnect.get_edge() for interconnect in self.interconnects]

        #
        self.design_vector_objects = components + interconnect_nodes

        # Get possible object collision pairs
        self.component_component_pairs = 1
        self.component_interconnect_pairs = 1
        self.interconnect_interconnect_pairs = 1
        self.structure_all_pairs = 1

        self.all_pairs = self.component_component_pairs+self.component_interconnect_pairs+self.interconnect_interconnect_pairs+self.structure_all_pairs

    def get_component_component_pairs(self):
        pass

    def get_component_interconnect_pairs(self):
        pass

    def get_interconnect_interconnect_pairs(self):
        pass

    def get_structure_all_pairs(self):
        pass

    def generate_random_layout(self):
        """
        Generates random layouts using a force-directed algorithm

        :return:
        """

        g = nx.MultiGraph()
        g.add_nodes_from(self.nodes)
        g.add_edges_from(self.edges)

        # Optimal distance between nodes
        k = 1

        # Dimension of layout
        dim = 3

        positions = nx.spring_layout(g, k=k, dim=dim)

        # Generate random angles too?

        # Now create a positions dictionary


        return positions

    def get_design_vector(self):
        pass

    def get_reference_positions(self):

        reference_positions_dict = {}

        for obj in self.objects:
            reference_positions_dict[obj]= obj.get_reference_position()

        return reference_positions_dict


    def get_positions(self):
        pass

    def get_radii(self):
        pass

    def set_reference_positions(self, new_reference_positions):

        for obj in self.design_vector_objects:
            obj.set_reference_position(new_reference_positions[obj])



    def set_positions(self):
        pass

    def set_rotations(self):
        pass



    def get_objective(self):
        pass

    def plot_layout(self):
        layout_plot_dict = {}

        for obj in self.objects:
            object_plot_dict = {}

            positions = obj.positions
            radii = obj.radii
            color = obj.color

            object_plot_dict['positions'] = positions
            object_plot_dict['radii'] = radii
            object_plot_dict['color'] = color

            layout_plot_dict[obj] = object_plot_dict

        plot(layout_plot_dict)
