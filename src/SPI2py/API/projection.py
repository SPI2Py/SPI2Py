import jax.numpy as jnp
from jax import grad, jacfwd, jacrev
from jax.scipy.stats import gaussian_kde
from openmdao.api import ExplicitComponent, Group
from openmdao.core.indepvarcomp import IndepVarComp

from ..models.projection.projection import calculate_pseudo_densities
from ..models.projection.projection_interconnects import calculate_densities
from ..models.utilities.aggregation import kreisselmeier_steinhauser_max
from ..models.projection.mesh_kernels import mdbd_1_kernel_positions, mdbd_1_kernel_radii
from ..models.projection.mesh_kernels import mdbd_9_kernel_positions, mdbd_9_kernel_radii
from ..models.projection.mesh_kernels import uniform_8_kernel_positions, uniform_8_kernel_radii
from ..models.projection.mesh_kernels import uniform_64_kernel_positions, uniform_64_kernel_radii
from ..models.projection.mesh_kernels import mdbd_kernel_positions, mdbd_kernel_radii


class Mesh(IndepVarComp):
    def initialize(self):

        self.options.declare('bounds', types=tuple, desc='Bounds of the mesh')
        self.options.declare('n_elements_per_unit_length', types=float, desc='Number of elements per unit length')

    def setup(self):

        # Get the options
        bounds = self.options['bounds']
        n_elements_per_unit_length = self.options['n_elements_per_unit_length']

        # Determine the number of elements in each direction
        x_min, x_max, y_min, y_max, z_min, z_max = bounds

        n_el_x = int(n_elements_per_unit_length * (x_max - x_min))
        n_el_y = int(n_elements_per_unit_length * (y_max - y_min))
        n_el_z = int(n_elements_per_unit_length * (z_max - z_min))

        element_length = 1 / n_elements_per_unit_length
        element_half_length = element_length / 2

        # Define the mesh grid positions
        x_grid_positions = jnp.linspace(x_min, x_max, n_el_x + 1)
        y_grid_positions = jnp.linspace(y_min, y_max, n_el_y + 1)
        z_grid_positions = jnp.linspace(z_min, z_max, n_el_z + 1)
        x_grid, y_grid, z_grid = jnp.meshgrid(x_grid_positions, y_grid_positions, z_grid_positions, indexing='ij')
        grid = jnp.stack((x_grid, y_grid, z_grid), axis=-1)

        # Define the mesh center points
        x_center_positions = jnp.linspace(x_min + element_half_length, element_length * n_el_x - element_half_length, n_el_x)
        y_center_positions = jnp.linspace(y_min + element_half_length, element_length * n_el_y - element_half_length, n_el_y)
        z_center_positions = jnp.linspace(z_min + element_half_length, element_length * n_el_z - element_half_length, n_el_z)
        x_centers, y_centers, z_centers = jnp.meshgrid(x_center_positions, y_center_positions, z_center_positions, indexing='ij')

        # Define the bounds of each mesh element
        x_min_element = x_centers - element_half_length
        x_max_element = x_centers + element_half_length
        y_min_element = y_centers - element_half_length
        y_max_element = y_centers + element_half_length
        z_min_element = z_centers - element_half_length
        z_max_element = z_centers + element_half_length
        element_bounds = jnp.stack((x_min_element, x_max_element, y_min_element, y_max_element, z_min_element, z_max_element), axis=-1)

        # Read the MDBD kernel
        kernel_positions = mdbd_1_kernel_positions
        kernel_radii = mdbd_1_kernel_radii

        kernel_positions = jnp.array(kernel_positions)
        kernel_radii = jnp.array(kernel_radii).reshape(-1, 1)

        # Scale the sphere positions
        kernel_positions = kernel_positions * element_length
        kernel_radii = kernel_radii * element_length

        meshgrid_centers = jnp.stack((x_centers, y_centers, z_centers), axis=-1)
        meshgrid_centers_expanded = jnp.expand_dims(meshgrid_centers, axis=3)

        all_points = meshgrid_centers_expanded + kernel_positions
        all_radii = jnp.zeros((n_el_x, n_el_y, n_el_z, 1, 1)) + kernel_radii

        # Calculate the kernel volume fraction
        kernel_volume = jnp.sum(4/3 * jnp.pi * kernel_radii ** 3)
        element_volume = element_length ** 3
        kernel_volume_fraction = kernel_volume / element_volume

        # Declare the outputs
        self.add_output('element_length', val=element_length)
        self.add_output('centers', val=meshgrid_centers)
        self.add_output('element_bounds', val=element_bounds)
        self.add_output('grid', val=grid)
        self.add_output('n_el_x', val=n_el_x)
        self.add_output('n_el_y', val=n_el_y)
        self.add_output('n_el_z', val=n_el_z)
        self.add_output('sample_points', val=all_points)
        self.add_output('sample_radii', val=all_radii)


class Projections(Group):
    def initialize(self):
        self.options.declare('n_comp_projections', types=int, desc='Number of component projections')
        self.options.declare('n_int_projections', types=int, desc='Number of interconnect projections')

    def setup(self):

        # Get the options
        n_comp_projections = self.options['n_comp_projections']
        n_int_projections = self.options['n_int_projections']

        # Projection counter
        i = 0

        # Add the projection components
        for _ in range(n_comp_projections):
            self.add_subsystem(f'projection_{i}', ProjectComponent())
            i += 1

        # Add the interconnect projection components
        for _ in range(n_int_projections):
            self.add_subsystem(f'projection_{i}', ProjectComponent())
            i += 1


class ProjectComponent(ExplicitComponent):
    """
    Calculates the pseudo-density of a set of points in a 3D grid
    """

    def initialize(self):
        self.options.declare('color', types=str, desc='Color of the projection', default='blue')

    def setup(self):

        # Mesh Inputs
        self.add_input('element_length', val=0)
        self.add_input('centers', shape_by_conn=True)
        self.add_input('element_bounds', shape_by_conn=True)
        self.add_input('sample_points', shape_by_conn=True)
        self.add_input('sample_radii', shape_by_conn=True)

        # Object Inputs
        self.add_input('sphere_positions', shape_by_conn=True)
        self.add_input('sphere_radii', shape_by_conn=True)
        self.add_input('volume', val=0.0)

        # Outputs
        self.add_output('pseudo_densities', compute_shape=lambda shapes: (shapes['centers'][0], shapes['centers'][1], shapes['centers'][2]))
        self.add_output('volume_estimation_error', val=0.0, desc='How accurately the projection represents the object')

    def setup_partials(self):
        self.declare_partials('pseudo_densities', 'sphere_positions')

    def compute(self, inputs, outputs):

        # Get the Mesh inputs
        element_length   = jnp.array(inputs['element_length'])
        element_bounds   = jnp.array(inputs['element_bounds'])
        sample_points    = jnp.array(inputs['sample_points'])
        sample_radii     = jnp.array(inputs['sample_radii'])
        sphere_positions = jnp.array(inputs['sphere_positions'])
        sphere_radii     = jnp.array(inputs['sphere_radii'])
        volume           = jnp.array(inputs['volume'])

        # Compute the pseudo-densities
        pseudo_densities = self._project(sphere_positions, sphere_radii, sample_points, sample_radii, element_bounds)

        # Compute the volume estimation error
        projected_volume = jnp.sum(pseudo_densities * element_length ** 3)
        volume_estimation_error = jnp.abs(volume - projected_volume) / volume

        # Write the outputs
        outputs['pseudo_densities'] = pseudo_densities
        outputs['volume_estimation_error'] = volume_estimation_error

    def compute_partials(self, inputs, partials):

        # Get the inputs
        element_bounds = jnp.array(inputs['element_bounds'])
        sample_points    = jnp.array(inputs['sample_points'])
        sample_radii     = jnp.array(inputs['sample_radii'])
        sphere_positions = jnp.array(inputs['sphere_positions'])
        sphere_radii     = jnp.array(inputs['sphere_radii'])


        # Calculate the Jacobian of the pseudo-densities
        jac_pseudo_densities = jacfwd(self._project)(sphere_positions, sphere_radii, sample_points, sample_radii, element_bounds)

        # Set the partials
        partials['pseudo_densities', 'sphere_positions'] = jac_pseudo_densities


    @staticmethod
    def _project(sphere_positions, sphere_radii, sample_points, sample_radii, element_bounds):
        pseudo_densities = calculate_pseudo_densities(sphere_positions, sphere_radii, sample_points, sample_radii, element_bounds)
        return pseudo_densities


class ProjectInterconnect(ExplicitComponent):

    def initialize(self):
        self.options.declare('color', types=str, desc='Color of the projection', default='blue')


    def setup(self):

        # Mesh Inputs
        self.add_input('element_length', val=0)
        self.add_input('centers', shape_by_conn=True)
        self.add_input('element_bounds', shape_by_conn=True)
        self.add_input('sample_points', shape_by_conn=True)
        self.add_input('sample_radii', shape_by_conn=True)

        # Object Inputs
        self.add_input('sphere_positions', shape_by_conn=True)
        self.add_input('sphere_radii', shape_by_conn=True)
        self.add_input('volume', val=0.0)

        # Outputs
        self.add_output('pseudo_densities',
                        compute_shape=lambda shapes: (shapes['centers'][0], shapes['centers'][1], shapes['centers'][2]))

    def setup_partials(self):
        self.declare_partials('*', '*')

    def compute(self, inputs, outputs):

        # Get the Mesh inputs
        element_length   = jnp.array(inputs['element_length'])
        element_bounds   = jnp.array(inputs['element_bounds'])
        sample_points    = jnp.array(inputs['sample_points'])
        sample_radii     = jnp.array(inputs['sample_radii'])
        sphere_positions = jnp.array(inputs['sphere_positions'])
        sphere_radii     = jnp.array(inputs['sphere_radii'])
        volume           = jnp.array(inputs['volume'])

        # Compute the pseudo-densities
        pseudo_densities = self._project(sample_points, sample_radii, sphere_positions, sphere_radii)

        # Compute the volume estimation error
        # projected_volume = jnp.sum(pseudo_densities * element_length ** 3)
        # volume_estimation_error = jnp.abs(volume - projected_volume) / volume

        # Write the outputs
        outputs['pseudo_densities'] = pseudo_densities
        # outputs['volume_estimation_error'] = volume_estimation_error

    # def compute_partials(self, inputs, partials):
    #
    #     # Get the inputs
    #     element_bounds = jnp.array(inputs['element_bounds'])
    #     sample_points    = jnp.array(inputs['sample_points'])
    #     sample_radii     = jnp.array(inputs['sample_radii'])
    #     sphere_positions = jnp.array(inputs['sphere_positions'])
    #     sphere_radii     = jnp.array(inputs['sphere_radii'])
    #     aabb = jnp.array(inputs['AABB'])
    #
    #     # Calculate the Jacobian of the pseudo-densities
    #     jac_pseudo_densities = jacfwd(self._project)(sphere_positions, sphere_radii, sample_points, sample_radii, aabb, element_bounds)
    #
    #     # Set the partials
    #     partials['pseudo_densities', 'sphere_positions'] = jac_pseudo_densities


    @staticmethod
    def _project(sample_points, sample_radii, sphere_positions, sphere_radii):

        import numpy as np
        def create_cylinders(points, radius):
            x1 = np.array(points[:-1])  # Start positions (-1, 3)
            x2 = np.array(points[1:])  # Stop positions (-1, 3)
            r = np.full((x1.shape[0], 1), radius)
            return x1, x2, r

        X1, X2, R = create_cylinders(sample_points, sample_radii)

        pseudo_densities = calculate_densities(sample_points, sample_radii, X1, X2, R)
        return pseudo_densities



class ProjectionAggregator(ExplicitComponent):

    def initialize(self):
        self.options.declare('n_projections', types=int, desc='Number of projections')
        self.options.declare('rho_min', types=(int, float), desc='Minimum value of the density', default=3e-3)

    def setup(self):

        # Get the options
        n_projections = self.options['n_projections']

        # Set the inputs
        self.add_input('element_length', val=0)

        for i in range(n_projections):
            self.add_input(f'pseudo_densities_{i}', shape_by_conn=True)

        # Set the outputs
        self.add_output('pseudo_densities', copy_shape='pseudo_densities_0')
        self.add_output('max_pseudo_density', val=0.0, desc='How much of each object overlaps/is out of bounds')

    def setup_partials(self):

        # Get the options
        n_projections = self.options['n_projections']

        # Set the partials
        for i in range(n_projections):
            self.declare_partials('pseudo_densities', f'pseudo_densities_{i}')
            self.declare_partials('max_pseudo_density', f'pseudo_densities_{i}')


    def compute(self, inputs, outputs):

        # Get the options
        n_projections = self.options['n_projections']
        rho_min = self.options['rho_min']

        # Get the inputs
        element_length = jnp.array(inputs['element_length'])
        pseudo_densities = [jnp.array(inputs[f'pseudo_densities_{i}']) for i in range(n_projections)]

        # Calculate the values
        aggregate_pseudo_densities, max_pseudo_density = self._aggregate_pseudo_densities(pseudo_densities, element_length, rho_min)

        # Write the outputs
        outputs['pseudo_densities'] = aggregate_pseudo_densities
        outputs['max_pseudo_density'] = max_pseudo_density

    def compute_partials(self, inputs, partials):

        # Get the options
        n_projections = self.options['n_projections']
        rho_min = self.options['rho_min']

        # Get the inputs
        element_length = jnp.array(inputs['element_length'])
        pseudo_densities = [jnp.array(inputs[f'pseudo_densities_{i}']) for i in range(n_projections)]

        # Calculate the partial derivatives
        jac_pseudo_densities, jac_max_pseudo_density = jacfwd(self._aggregate_pseudo_densities)(pseudo_densities, element_length, rho_min)

        # Set the partial derivatives
        jacs = zip(jac_pseudo_densities, jac_max_pseudo_density)
        for i, (jac_pseudo_densities_i, jac_max_pseudo_density_i) in enumerate(jacs):
            partials['pseudo_densities', f'pseudo_densities_{i}'] = jac_pseudo_densities_i
            partials['max_pseudo_density', f'pseudo_densities_{i}'] = jac_max_pseudo_density_i

    @staticmethod
    def _aggregate_pseudo_densities(pseudo_densities, element_length, rho_min):

        # Aggregate the pseudo-densities
        aggregate_pseudo_densities = jnp.zeros_like(pseudo_densities[0])
        for pseudo_density in pseudo_densities:
            aggregate_pseudo_densities += pseudo_density

        # Ensure that no pseudo-density is below the minimum value
        aggregate_pseudo_densities = jnp.maximum(aggregate_pseudo_densities, rho_min)

        # TODO rethink max if we need to overlap interconnects and components

        # Calculate the maximum pseudo-density
        max_pseudo_density = kreisselmeier_steinhauser_max(aggregate_pseudo_densities)

        return aggregate_pseudo_densities, max_pseudo_density

######

