#ifndef QTGL_DETAIL_KEYFRAME_HPP_INCLUDED
#   define QTGL_DETAIL_KEYFRAME_HPP_INCLUDED

#   include <qtgl/detail/keyframe_cache.hpp>
#   include <utility/assumptions.hpp>
#   include <vector>
#   include <algorithm>
#   include <utility>

namespace qtgl {


struct  keyframe : public detail::async_resource_accessor_base<detail::keyframe_data>
{
    explicit keyframe(boost::filesystem::path const&  path)
        : detail::async_resource_accessor_base<detail::keyframe_data>(path,1U)
    {}

    float_32_bit  get_time_point() const { return resource_ptr()->time_point(); }

    std::vector<angeo::coordinate_system> const&  get_coord_systems() const
    { return resource_ptr()->coord_systems(); }
};


struct keyframes
{
    keyframes(std::vector<boost::filesystem::path> const  paths)
        : m_keyframes(paths.cbegin(), paths.cend())
        , m_load_state(detail::ASYNC_LOAD_STATE::IN_PROGRESS)
    {
        ASSUMPTION(!m_keyframes.empty());
    }

    bool  loaded_successfully() const
    {
        update_load_state();
        return _loaded_successfully();
    }
    
    bool  load_failed() const
    {
        update_load_state();
        return m_load_state == detail::ASYNC_LOAD_STATE::FINISHED_WITH_ERROR;
    }

    std::vector<qtgl::keyframe> const&  get_keyframes() const { return m_keyframes; }

    float_32_bit  start_time_point() const { return m_keyframes.front().get_time_point(); }
    float_32_bit  end_time_point() const { return m_keyframes.back().get_time_point(); }
    float_32_bit  duration() const { return end_time_point() - start_time_point(); }

    std::size_t  num_keyframes() const { return m_keyframes.size(); }
    keyframe const&  keyframe_at(std::size_t const  index) const { return m_keyframes.at(index); }

    float_32_bit  time_point_at(std::size_t const  index) const { return keyframe_at(index).get_time_point(); }
    std::size_t  num_coord_systems_per_keyframe() const { return m_keyframes.front().get_coord_systems().size(); }
    angeo::coordinate_system const&  coord_system_at(
            std::size_t const  keyframe_index,
            std::size_t const  coord_system_index) const
    { return keyframe_at(keyframe_index).get_coord_systems().at(coord_system_index); }

private:

    bool  _loaded_successfully() const
    {
        return m_load_state == detail::ASYNC_LOAD_STATE::FINISHED_SUCCESSFULLY;
    }

    void  update_load_state() const { const_cast<keyframes*>(this)->_update_load_state(); }
    void  _update_load_state();

    std::vector<qtgl::keyframe>  m_keyframes;
    detail::ASYNC_LOAD_STATE  m_load_state;
};


std::pair<std::size_t, std::size_t>  find_indices_of_keyframes_to_interpolate_for_time(
        keyframes const&  keyframes,
        float_32_bit const  time_point
        );


float_32_bit  compute_interpolation_parameter(
        float_32_bit const  time_point,
        float_32_bit const  keyframe_start_time_point,
        float_32_bit const  keyframe_end_time_point
        );


void  compute_coord_system_of_frame_of_keyframe_animation(
        keyframes const&  keyframes,
        std::pair<std::size_t, std::size_t> const  indices_of_keyframe_to_interpolate,
        std::size_t const  index_of_coord_system_in_keyframes,
        float_32_bit const  interpolation_param, // in range <0,1>
        angeo::coordinate_system&  output
        );


void  compute_frame_of_keyframe_animation(
        keyframes const&  keyframes,
        std::pair<std::size_t, std::size_t> const  indices_of_keyframe_to_interpolate,
        float_32_bit const  interpolation_param, // in range <0,1>
        std::vector<angeo::coordinate_system>&  output
        );


void  compute_frame_of_keyframe_animation(
        keyframes const&  keyframes,
        std::pair<std::size_t, std::size_t> const  indices_of_keyframe_to_interpolate,
        float_32_bit const  interpolation_param, // in range <0,1>
        std::vector<matrix44>&  output
        );


void  compute_frame_of_keyframe_animation(
        keyframes const&  keyframes,
        float_32_bit const  time_point,
        std::vector<angeo::coordinate_system>&  output
        );


void  compute_frame_of_keyframe_animation(
        keyframes const&  keyframes,
        float_32_bit const  time_point,
        std::vector<matrix44>&  output  // the results will be composed with the current data.
        );


void  compute_frame_of_keyframe_animation(
        keyframes const&  keyframes,
        matrix44 const&  target_space, // typically, the target space is a camera space, i.e. view_projection_matrix
        float_32_bit const  time_point,
        std::vector<matrix44>&  output // old content won't be used and it will be owerwritten by the computed data.
        );


float_32_bit  update_animation_time(
        float_32_bit  current_animation_time_point,
        float_32_bit const  time_delta,
        float_32_bit const  keyframes_start_time,
        float_32_bit const  keyframes_end_time
        );


}

#endif
