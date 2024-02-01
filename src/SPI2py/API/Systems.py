import numpy as np
import torch
from openmdao.api import ExplicitComponent

from ..models.geometry.bounding_box_volume import bounding_box_bounds, bounding_box_volume



class System(ExplicitComponent):

    def initialize(self):
        self.options.declare('num_components', types=int)


    def setup(self):

        num_components = self.options['num_components']
        for i in range(num_components):
            self.add_input(f'comp_{i}_sphere_positions', shape_by_conn=True)
            self.add_input(f'comp_{i}_sphere_radii', shape_by_conn=True)

        self.add_output('bounding_box_volume', val=0)
        self.add_output('bounding_box_bounds', shape=(1, 6))
        # self.add_output('constraints', val=torch.zeros(1))

    def setup_partials(self):
        # for i in range(self.options['num_components']):
        #     self.declare_partials('bounding box volume', f'comp_{i}_sphere_positions')
        self.declare_partials('*', '*')

    def compute(self, inputs, outputs):

        # Get the input variables
        # sphere_positions = inputs['sphere_positions']
        # sphere_radii = inputs['sphere_radii']
        sphere_positions = [inputs[f'comp_{i}_sphere_positions'] for i in range(self.options['num_components']) ]
        sphere_radii = [inputs[f'comp_{i}_sphere_radii'] for i in range(self.options['num_components']) ]

        # Vertically stack the sphere positions and radii
        sphere_positions = np.vstack(sphere_positions)
        sphere_radii = np.vstack(sphere_radii)

        # Convert the inputs to torch tensors
        sphere_positions = torch.tensor(sphere_positions, dtype=torch.float64)
        sphere_radii = torch.tensor(sphere_radii, dtype=torch.float64)

        # Calculate the bounding box volume
        bb_bounds = bounding_box_bounds(sphere_positions, sphere_radii)
        bb_volume = bounding_box_volume(bb_bounds)

        # Convert the outputs to numpy arrays
        bb_bounds = bb_bounds.detach().numpy()
        bb_volume = bb_volume.detach().numpy()

        # Set the outputs
        outputs['bounding_box_bounds'] = bb_bounds
        outputs['bounding_box_volume'] = bb_volume
        # outputs['constraints'] = constraints

    # def compute_partials(self, inputs, partials):
    #     pass


# class _System:
#     def __init__(self, components, interconnects):
#
#
#         self.components = components
#         self.interconnects = interconnects
#         self.objects = self.components + self.interconnects
#
#
#         self.component_pairs = self.get_component_pairs()
#         self.interconnect_pairs = self.get_interconnect_pairs()
#         self.component_interconnect_pairs = self.get_component_interconnect_pairs()
#
#
#         objective = self.input['problem']['objective']
#         self.set_objective(objective)
#
#         self.translations_shape = (self.num_components, 3)
#         self.rotations_shape = (self.num_components, 3)
#         self.routings_shape = (self.num_interconnects, self.num_nodes, 3)
#
#     # def set_objective(self, objective: str):
#     #
#     #     """
#     #     Add an objective to the design study.
#     #
#     #     :param objective: The objective function to be added.
#     #     :param options: The options for the objective function.
#     #     """
#     #
#     #     # SELECT THE OBJECTIVE FUNCTION HANDLE
#     #
#     #     if objective == 'bounding box volume':
#     #         _objective_function = bounding_box_volume
#     #     else:
#     #         raise NotImplementedError
#     #
#     #     def objective_function(positions):
#     #         return _objective_function(positions)
#     #
#     #     self.objective = objective_function
#     #
#     # def calculate_positions(self, translations, rotations, routings):
#     #
#     #     objects_dict = {}
#     #
#     #     for component, translation, rotation in zip(self.components, translations, rotations):
#     #         object_dict = component.calculate_positions(translation, rotation)
#     #         objects_dict = {**objects_dict, **object_dict}
#     #
#     #     for interconnect, routing in zip(self.interconnects, routings):
#     #         object_dict = interconnect.calculate_positions(routing)
#     #         objects_dict = {**objects_dict, **object_dict}
#     #
#     #     return objects_dict
#
#     def get_component_pairs(self):
#         component_component_pairs = list(combinations(self.components, 2))
#         return component_component_pairs
#
#     def get_interconnect_pairs(self):
#         interconnect_interconnect_pairs = list(combinations(self.interconnects, 2))
#         return interconnect_interconnect_pairs
#
#     def get_component_interconnect_pairs(self):
#         component_interconnect_pairs = list(product(self.components, self.interconnects))
#         return component_interconnect_pairs
#
#     def collision_component_pairs(self, positions_dict):
#         signed_distance_vals = aggregate_signed_distance(positions_dict, self.component_pairs)
#         max_signed_distance = kreisselmeier_steinhauser(signed_distance_vals)
#         return max_signed_distance
#
#     def collision_interconnect_pairs(self, positions_dict):
#         signed_distance_vals = aggregate_signed_distance(positions_dict, self.interconnect_pairs)
#         max_signed_distance = kreisselmeier_steinhauser(signed_distance_vals)
#         return max_signed_distance
#
#     def collision_component_interconnect_pairs(self, positions_dict):
#         # TODO Remove tolerance
#         signed_distance_vals = aggregate_signed_distance(positions_dict, self.component_interconnect_pairs)
#         max_signed_distance = kreisselmeier_steinhauser(signed_distance_vals) - 0.2
#         return max_signed_distance
#
#
#
#     def calculate_constraints(self, translations, rotations, routings):
#
#         positions_dict = self.calculate_positions(translations, rotations, routings)
#
#         # g_component_pairs = self.collision_component_pairs(positions_dict)
#         # g_interconnect_pairs = self.collision_interconnect_pairs(positions_dict)
#         # g_component_interconnect_pairs = self.collision_component_interconnect_pairs(positions_dict)
#         # g = torch.tensor((g_component_pairs, g_interconnect_pairs, g_component_interconnect_pairs))
#
#         # TODO Add other constraints back in
#         g = self.collision_component_pairs(positions_dict)
#
#         return g
#
#