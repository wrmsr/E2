#ifndef E2_TOOL_GFXTUNER_WINDOW_TABS_TAB_SCENE_HPP_INCLUDED
#   define E2_TOOL_GFXTUNER_WINDOW_TABS_TAB_SCENE_HPP_INCLUDED

#   include <angeo/tensor_math.hpp>
#   include <gfxtuner/scene.hpp>
#   include <boost/filesystem.hpp>
#   include <boost/filesystem/path.hpp>
#   include <QWidget>
#   include <QTreeWidget>
#   include <QColor>
#   include <string>


struct  program_window;


namespace window_tabs { namespace tab_scene {


struct  widgets
{
    widgets(program_window* const  wnd);

    program_window*  wnd() const { return m_wnd; }

    QTreeWidget*  scene_tree() const { return m_scene_tree; }

    QLineEdit* coord_system_pos_x() const { return m_coord_system_pos_x; }
    QLineEdit* coord_system_pos_y() const { return m_coord_system_pos_y; }
    QLineEdit* coord_system_pos_z() const { return m_coord_system_pos_z; }

    QLineEdit* coord_system_rot_w() const { return m_coord_system_rot_w; }
    QLineEdit* coord_system_rot_x() const { return m_coord_system_rot_x; }
    QLineEdit* coord_system_rot_y() const { return m_coord_system_rot_y; }
    QLineEdit* coord_system_rot_z() const { return m_coord_system_rot_z; }

    QLineEdit* coord_system_yaw() const { return m_coord_system_yaw; }
    QLineEdit* coord_system_pitch() const { return m_coord_system_pitch; }
    QLineEdit* coord_system_roll() const { return m_coord_system_roll; }

    void  on_simulator_started() { clear_scene(); }

    void  on_scene_hierarchy_item_selected();
    void  on_scene_insert_coord_system();
    void  on_scene_insert_batch();
    void  on_scene_erase_selected();

    void  on_coord_system_pos_changed();
    void  on_coord_system_rot_changed();
    void  on_coord_system_rot_tait_bryan_changed();

    void  coord_system_position_listener();
    void  coord_system_rotation_listener();

    void  clear_scene();
    void  open_scene(boost::filesystem::path const&  scene_root_dir);
    void  save_scene(boost::filesystem::path const&  scene_root_dir);

    void  save();

private:

    QTreeWidgetItem*  insert_coord_system(
                std::string const&  name,
                vector3 const&  origin,
                quaternion const&  orientation,
                QTreeWidgetItem* const  parent_tree_item);
    QTreeWidgetItem*  insert_batch(
                QTreeWidgetItem* const  node_item,
                std::string const&  batch_name,
                boost::filesystem::path const  batch_pathname
                );

    void  update_coord_system_location_widgets();
    void  enable_coord_system_location_widgets(bool const  state);
    void  refresh_text_in_coord_system_location_widgets(scene_node_ptr const  node_ptr);
    void  refresh_text_in_coord_system_rotation_widgets(quaternion const&  q);

    program_window*  m_wnd;

    QTreeWidget*  m_scene_tree;
    QIcon  m_node_icon;
    QIcon  m_batch_icon;

    QLineEdit*  m_coord_system_pos_x;
    QLineEdit*  m_coord_system_pos_y;
    QLineEdit*  m_coord_system_pos_z;

    QLineEdit*  m_coord_system_rot_w;
    QLineEdit*  m_coord_system_rot_x;
    QLineEdit*  m_coord_system_rot_y;
    QLineEdit*  m_coord_system_rot_z;

    QLineEdit*  m_coord_system_yaw;
    QLineEdit*  m_coord_system_pitch;
    QLineEdit*  m_coord_system_roll;
};


QWidget*  make_scene_tab_content(widgets const&  w);


}}

#endif
