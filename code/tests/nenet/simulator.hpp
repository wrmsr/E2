#ifndef SIMULATOR_HPP_INCLUDED
#   define SIMULATOR_HPP_INCLUDED

#   include "./nenet.hpp"
#   include <qtgl/real_time_simulator.hpp>
#   include <qtgl/camera.hpp>
#   include <qtgl/free_fly.hpp>
#   include <qtgl/draw.hpp>
#   include <string>
#   include <memory>


struct simulator : public qtgl::real_time_simulator
{
    simulator(vector3 const&  initial_clear_colour, bool const  paused,
              float_64_bit const  desired_number_of_simulated_seconds_per_real_time_second);
    ~simulator();
    void next_round(float_64_bit const  seconds_from_previous_call,
                    bool const  is_this_pure_redraw_request);

    std::shared_ptr<nenet>  nenet() const noexcept { return m_nenet; }

    void  set_clear_color(vector3 const&  colour) { qtgl::glapi().glClearColor(colour(0), colour(1), colour(2), 1.0f); }

    vector3 const&  get_camera_position() const { return m_camera->coordinate_system()->origin(); }
    quaternion const&  get_camera_orientation() const { return m_camera->coordinate_system()->orientation(); }

    void  set_camera_position(vector3 const&  position) { m_camera->coordinate_system()->set_origin(position); }
    void  set_camera_orientation(quaternion const&  orientation) { m_camera->coordinate_system()->set_orientation(orientation); }

    float_64_bit  spent_real_time() const noexcept { return m_spent_real_time; }
    natural_64_bit  nenet_num_updates() const noexcept { return nenet()->num_passed_updates(); }
    float_64_bit  spent_simulation_time() const { return nenet_num_updates() * update_time_step_in_seconds(); }
    float_64_bit  desired_number_of_simulated_seconds_per_real_time_second() const { return m_desired_number_of_simulated_seconds_per_real_time_second; }
    void set_desired_number_of_simulated_seconds_per_real_time_second(float_64_bit const  value);

    bool  paused() const noexcept { return m_paused; }

private:
    std::shared_ptr<::nenet>  m_nenet;
    float_64_bit  m_spent_real_time;
    bool  m_paused;
    float_64_bit  m_desired_number_of_simulated_seconds_per_real_time_second;

    cell::pos_map::const_iterator  m_selected_cell;
    scalar  m_selected_rot_angle;

    qtgl::camera_perspective_ptr  m_camera;
    qtgl::free_fly_config  m_free_fly_config;

    qtgl::batch_ptr  m_batch_grid;
    qtgl::batch_ptr  m_batch_cell;
    qtgl::batch_ptr  m_batch_input_spot;
    qtgl::batch_ptr  m_batch_output_terminal;

    qtgl::batch_ptr  m_selected_cell_input_spot_lines;
    qtgl::batch_ptr  m_selected_cell_output_terminal_lines;
};

namespace notifications {


inline std::string  camera_position_updated() { return "CAMERA_POSITION_UPDATED"; }
inline std::string  camera_orientation_updated() { return "CAMERA_ORIENTATION_UPDATED"; }
inline std::string  paused() { return "PAUSED"; }


}


#endif
