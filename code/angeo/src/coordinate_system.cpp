#include <angeo/coordinate_system.hpp>
#include <utility/assumptions.hpp>
#include <utility/invariants.hpp>

namespace angeo {


coordinate_system_ptr  coordinate_system::create(vector3 const&  origin, quaternion const&  orientation)
{
    return coordinate_system_ptr( new coordinate_system(origin,orientation) );
}

coordinate_system::coordinate_system(vector3 const&  origin, quaternion const&  orientation)
    : m_origin(origin)
    , m_orientation(orientation)
{
    ASSUMPTION(are_equal(length_squared(m_orientation),1));
}


void coordinate_system::set_orientation(quaternion const&  new_normalised_orientation)
{
    ASSUMPTION(are_equal(length_squared(new_normalised_orientation),1));
    m_orientation = new_normalised_orientation;
}


void  translate(coordinate_system&  coord_system, vector3 const&  shift)
{
    coord_system.set_origin( coord_system.origin() + shift );
}


void  rotate(coordinate_system&  coord_system, quaternion const&  rotation)
{
    ASSUMPTION(are_equal(length_squared(rotation),1));
    quaternion  composed = rotation * coord_system.orientation();
    normalise(composed);
    coord_system.set_orientation( composed );
}


void  from_base_matrix(coordinate_system const&  coord_system, matrix44&  output)
{
    vector3 const&  p = coord_system.origin();
    matrix33 const  R = coord_system.orientation().toRotationMatrix();
    output <<
            R(0,0), R(0,1), R(0,2), p(0),
            R(1,0), R(1,1), R(1,2), p(1),
            R(2,0), R(2,1), R(2,2), p(2),
            0.0f,   0.0f,   0.0f,   1.0f
            ;
}


void  to_base_matrix(coordinate_system const&  coord_system, matrix44&  output)
{
    //matrix44  transform_matrix;
    //from_base_matrix(coord_system,transform_matrix);
    //output = inverse(transform_matrix);
    vector3 const&  p = coord_system.origin();
    matrix33 const  R = coord_system.orientation().toRotationMatrix();
    output <<
            R(0,0), R(1,0), R(2,0), -(R(0,0) * p(0) + R(1,0) * p(1) + R(2,0) * p(2)),
            R(0,1), R(1,1), R(2,1), -(R(0,1) * p(0) + R(1,1) * p(1) + R(2,1) * p(2)),
            R(0,2), R(1,2), R(2,2), -(R(0,2) * p(0) + R(1,2) * p(1) + R(2,2) * p(2)),
            0.0f,   0.0f,   0.0f,   1.0f
            ;
}


vector3  axis(coordinate_system const&  coord_system, natural_8_bit const  axis_index)
{
    ASSUMPTION(axis_index == 0U || axis_index == 1U || axis_index == 2U);
    matrix33 const  rotation = quaternion_to_rotation_matrix(coord_system.orientation());
    return vector3(rotation(0,axis_index),rotation(1,axis_index),rotation(2,axis_index));
}

vector3  axis_x(coordinate_system const&  coord_system)
{
    return axis(coord_system,0U);
}

vector3  axis_y(coordinate_system const&  coord_system)
{
    return axis(coord_system,1U);
}

vector3  axis_z(coordinate_system const&  coord_system)
{
    return axis(coord_system,2U);
}


void  interpolate_linear(
        coordinate_system const&  head,
        coordinate_system const&  tail,
        float_32_bit const  parameter, // it must be in range <0,1>
        coordinate_system&  result
        )
{
    result.set_origin(::interpolate_linear(head.origin(),tail.origin(),parameter));
    result.set_orientation(::interpolate_linear(head.orientation(),tail.orientation(),parameter));
}

void  interpolate_spherical(
        coordinate_system const&  head,
        coordinate_system const&  tail,
        float_32_bit const  parameter, // it must be in range <0,1>
        coordinate_system&  result
        )
{
    result.set_origin(::interpolate_linear(head.origin(),tail.origin(),parameter));
    result.set_orientation(::interpolate_spherical(head.orientation(),tail.orientation(),parameter));
}


}
