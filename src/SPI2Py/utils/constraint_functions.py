"""



"""


from utils.distance_calculations import min_spheres_spheres_interference


def interference_component_component(x, layout):
    """
    Checks for the maximum collision between two ojects

    :param x:
    :param layout:
    :return:
    """

    # Calculate the positions of all spheres in layout given design vector x
    positions_dict = layout.get_positions(x)

    # Calculate the interferences between each sphere of each object pair
    interferences = []
    for obj1, obj2 in layout.component_component_pairs:

        positions_a = positions_dict[obj1]
        radii_a = obj1.radii.reshape(-1, 1)

        positions_b = positions_dict[obj2]
        radii_b = obj2.radii.reshape(-1, 1)

        dist = min_spheres_spheres_interference(positions_a, radii_a, positions_b, radii_b)

        interferences.append(dist)

        max_interference = max(interferences)

    return max_interference


def interference_component_interconnect(x, layout):

    # Calculate the positions of all spheres in layout given design vector x
    positions_dict = layout.get_positions(x)

    # Calculate the interferences between each sphere of each object pair
    interferences = []
    for obj1, obj2 in layout.component_interconnect_pairs:
        positions_a = positions_dict[obj1]
        radii_a = obj1.radii.reshape(-1, 1)

        positions_b = positions_dict[obj2]
        radii_b = obj2.radii.reshape(-1, 1)

        dist = min_spheres_spheres_interference(positions_a, radii_a, positions_b, radii_b)

        interferences.append(dist)

        max_interference = max(interferences)

    return max_interference


def interference_interconnect_interconnect(x, layout):

    # Calculate the positions of all spheres in layout given design vector x
    positions_dict = layout.get_positions(x)

    # Calculate the interferences between each sphere of each object pair
    interferences = []
    for obj1, obj2 in layout.interconnect_interconnect_pairs:
        positions_a = positions_dict[obj1]
        radii_a = obj1.radii.reshape(-1, 1)

        positions_b = positions_dict[obj2]
        radii_b = obj2.radii.reshape(-1, 1)

        dist = min_spheres_spheres_interference(positions_a, radii_a, positions_b, radii_b)

        interferences.append(dist)

        max_interference = max(interferences)

    return max_interference


def interference_structure_all(x, layout):
    # Calculate the positions of all spheres in layout given design vector x
    positions_dict = layout.get_positions(x)

    # Calculate the interferences between each sphere of each object pair
    interferences = []
    for obj1, obj2 in layout.structure_all_pairs:
        positions_a = positions_dict[obj1]
        radii_a = obj1.radii.reshape(-1, 1)

        positions_b = positions_dict[obj2]
        radii_b = obj2.radii.reshape(-1, 1)

        dist = min_spheres_spheres_interference(positions_a, radii_a, positions_b, radii_b)

        interferences.append(dist)

        max_interference = max(interferences)

    return max_interference

