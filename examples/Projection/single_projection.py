"""
Example 1:  Simple optimization of a 3D layout
Author:     Chad Peterson
"""

import numpy as np
import openmdao.api as om
import torch

from SPI2py.API.system import System
from SPI2py.API.utilities import Multiplexer, MaxAggregator
from SPI2py.API.projection import Projection, Projections, Mesh
from SPI2py.API.constraints import VolumeFractionConstraint
from SPI2py.models.utilities.visualization import plot_problem
from SPI2py.models.utilities.inputs import read_input_file
from SPI2py.API.objectives import BoundingBoxVolume
from SPI2py.API.utilities import Multiplexer, estimate_partial_derivative_memory, estimate_projection_error

# Set the random seed for reproducibility
np.random.seed(0)

# Set the default data type
torch.set_default_dtype(torch.float64)

# Read the input file
input_file = read_input_file('input_single_projection.toml')

# Initialize the problem
prob = om.Problem()
model = prob.model

# Mesh Parameters
# bounds = (3, 11, 3, 11, 0, 3)
# bounds = (0, 8, 1, 8, 0, 3)
bounds = (0, 5, 0, 5, 0, 3) # TODO FIX nonzero bounds
n_elements_per_unit_length = 1.0  # 1.0  # 6.0

# System Parameters
n_components = 1
n_points = 4
n_points_per_object = [n_points for _ in range(n_components)]


# Initialize the groups
model.add_subsystem('system', System(input_dict=input_file, upper=7, lower=0))
model.add_subsystem('mesh', Mesh(bounds=bounds, n_elements_per_unit_length=n_elements_per_unit_length,
                                 mdbd_unit_cube_filepath='mdbd_unit_cube.xyzr', mdbd_unit_cube_min_radius=0.1))
model.add_subsystem('projections', Projections(n_comp_projections=n_components, n_int_projections=0))

# TODO Promote?
model.connect('mesh.element_length', 'projections.projection_0.element_length')
model.connect('mesh.x_centers', 'projections.projection_0.x_centers')
model.connect('mesh.y_centers', 'projections.projection_0.y_centers')
model.connect('mesh.z_centers', 'projections.projection_0.z_centers')

model.connect('mesh.all_points', 'projections.projection_0.all_points')
model.connect('mesh.all_radii', 'projections.projection_0.all_radii')


model.connect('system.components.comp_0.transformed_sphere_positions', 'projections.projection_0.sphere_positions')
model.connect('system.components.comp_0.transformed_sphere_radii', 'projections.projection_0.sphere_radii')


# Set the initial state
prob.setup()


# Configure the system
prob.set_val('system.components.comp_0.translation', [2, 2, 1.5])
prob.set_val('system.components.comp_0.rotation', [0, 0, 0])
prob.set_val('projections.projection_0.highlight_element_index', [1, 2, 1])


prob.run_model()


# estimate_projection_error(prob,
#                           'system.components.comp_0.sphere_radii',
#                           'system.components.comp_0.translation',
#                           'projections.projection_0.volume',
#                           [5, 5, 1.5],
#                           5, 0.15)

# Debugging
ix, iy, iz = prob.get_val('projections.projection_0.highlight_element_index')
element_index = [int(ix), int(iy), int(iz)]
pseudo_densities = prob.get_val('projections.projection_0.element_pseudo_densities')

print("Checking element: ", element_index)
print("Pseudo-Density: ", pseudo_densities[element_index[0], element_index[1], element_index[2]])

# Check the initial state
plot_problem(prob)

print('Done')



# print('Number of elements:', prob.get_val('mesh.mesh_shape').size)






