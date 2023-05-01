import numpy as np
from SPI2py.group_model.component_spatial.distance_calculations import minimum_distance_capsule_capsule


def test_capsule_capsule_tangent_1():

    a = np.array([0., 0., 0.])
    b = np.array([1., 0., 0.])
    ab_radii = 0.5

    c = np.array([0., 0., 1.])
    d = np.array([1., 0., 1.])
    cd_radii = 0.5

    dist = minimum_distance_capsule_capsule(a, b, ab_radii, c, d, cd_radii)

    assert np.isclose(dist, 0)

def test_capsule_capsule_nonoverlap_1():

    a = np.array([0., 0., 0.])
    b = np.array([1., 0., 0.])
    ab_radii = np.array([0.5])

    c = np.array([0., 0., 2.])
    d = np.array([1., 0., 2.])
    cd_radii = np.array([0.5])

    dist = minimum_distance_capsule_capsule(a, b, ab_radii, c, d, cd_radii)

    assert np.isclose(dist, -1.0)


# AB is a Line Segment and CD is a Line Segment


def test_capsule_capsule_fully_overlapping():

    a = np.array([0., 0., 0.])
    b = np.array([1., 0., 0.])
    ab_radii = 0.5
    c = np.array([0., 0., 0.])
    d = np.array([1., 0., 0.])
    cd_radii = 0.5

    dist = minimum_distance_capsule_capsule(a, b, ab_radii, c, d, cd_radii)

    assert np.isclose(dist, 1.0)


# def test_parallel_horizontal_within_range():
#
#     a = np.array([0., 0., 0.])
#     b = np.array([1., 0., 0.])
#     c = np.array([0., 0., 1.])
#     d = np.array([1., 0., 1.])
#
#     dist, _ = minimum_distance_capsule_capsule(a, b, c, d)
#
#     assert np.isclose(dist, 1.0)
#
#
# def test_parallel_horizontal_out_of_range():
#
#     a = np.array([0., 0., 0.])
#     b = np.array([1., 0., 0.])
#     c = np.array([2., 0., 1.])
#     d = np.array([3., 0., 1.])
#
#     dist, _ = minimum_distance_capsule_capsule(a, b, c, d)
#
#     expected_dist = np.linalg.norm(c-b)
#
#     assert np.isclose(dist, expected_dist)
#
#
# def test_parallel_horizontal_along_same_axis():
#
#     a = np.array([0., 0., 0.])
#     b = np.array([1., 0., 0.])
#     c = np.array([2., 0., 0.])
#     d = np.array([3., 0., 0.])
#
#     dist, _ = minimum_distance_capsule_capsule(a, b, c, d)
#
#     assert np.isclose(dist, 1.0)
#
#
# def test_parallel_vertical_within_range():
#
#     a = np.array([0., 0., 0.])
#     b = np.array([0., 1., 0.])
#     c = np.array([0., 0., 1.])
#     d = np.array([0., 1., 1.])
#
#     dist, _ = minimum_distance_capsule_capsule(a, b, c, d)
#
#     assert np.isclose(dist, 1.0)
#
#
# def test_parallel_vertical_out_of_range():
#
#     a = np.array([0., 0., 0.])
#     b = np.array([0., 1., 0.])
#     c = np.array([1., 2., 0.])
#     d = np.array([1., 3., 0.])
#
#     dist, _ = minimum_distance_capsule_capsule(a, b, c, d)
#
#     expected_dist = np.linalg.norm(c - b)
#
#     assert np.isclose(dist, expected_dist)
#
#
# def test_skew():
#
#     a = np.array([0., 0., 0.])
#     b = np.array([1., 0., 0.])
#     c = np.array([0., 0., 2.])
#     d = np.array([1., 0., 1.])
#
#     dist, _ = minimum_distance_capsule_capsule(a, b, c, d)
#
#     assert np.isclose(dist, 1.0)

