#ifndef E2_TOOL_NETVIEWER_WINDOW_TABS_TAB_CAMERA_HPP_INCLUDED
#   define E2_TOOL_NETVIEWER_WINDOW_TABS_TAB_CAMERA_HPP_INCLUDED

#   include <utility/tensor_math.hpp>
#   include <boost/property_tree/ptree.hpp>
#   include <QWidget>
#   include <QLineEdit>
#   include <QCheckBox>


struct  program_window;


namespace window_tabs { namespace tab_camera {


struct  widgets
{
    widgets(program_window* const  wnd);

    program_window* wnd() const noexcept;

    QLineEdit* camera_pos_x() const noexcept;
    QLineEdit* camera_pos_y() const noexcept;
    QLineEdit* camera_pos_z() const noexcept;

    QLineEdit* camera_rot_w() const noexcept;
    QLineEdit* camera_rot_x() const noexcept;
    QLineEdit* camera_rot_y() const noexcept;
    QLineEdit* camera_rot_z() const noexcept;

    QLineEdit* camera_yaw() const noexcept;
    QLineEdit* camera_pitch() const noexcept;
    QLineEdit* camera_roll() const noexcept;

    QCheckBox* camera_save_pos_rot() const noexcept;

    void  on_camera_pos_changed();
    void  camera_position_listener();

    void  on_camera_rot_changed();
    void  on_camera_rot_tait_bryan_changed();
    void  camera_rotation_listener();
    void  update_camera_rot_widgets(quaternion const&  q);

    void  save();

private:
    program_window*  m_wnd;

    QLineEdit*  m_camera_pos_x;
    QLineEdit*  m_camera_pos_y;
    QLineEdit*  m_camera_pos_z;

    QLineEdit*  m_camera_rot_w;
    QLineEdit*  m_camera_rot_x;
    QLineEdit*  m_camera_rot_y;
    QLineEdit*  m_camera_rot_z;

    QLineEdit*  m_camera_yaw;
    QLineEdit*  m_camera_pitch;
    QLineEdit*  m_camera_roll;

    QCheckBox*  m_camera_save_pos_rot;
};


QWidget*  make_camera_tab_content(widgets const&  w);



}}

#endif
