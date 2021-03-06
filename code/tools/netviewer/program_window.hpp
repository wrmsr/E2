#ifndef E2_TOOL_NETVIEWER_PROGRAM_WINDOW_HPP_INCLUDED
#   define E2_TOOL_NETVIEWER_PROGRAM_WINDOW_HPP_INCLUDED

#   include <netviewer/simulator.hpp>
#   include <netviewer/window_tabs/tab_draw.hpp>
#   include <netviewer/window_tabs/tab_network.hpp>
#   include <netviewer/window_tabs/tab_selected.hpp>
#   include <netviewer/window_tabs/tab_performance.hpp>
#   include <netviewer/status_bar.hpp>
#   include <netviewer/menu_bar.hpp>
#   include <qtgl/window.hpp>
#   include <boost/property_tree/ptree.hpp>
#   include <boost/filesystem/path.hpp>
#   include <QMainWindow>
#   include <QWidget>
#   include <QSplitter>
#   include <QTabWidget>
#   include <QColor>
#   include <QEvent>
#   include <QTimerEvent>
#   include <QCloseEvent>
#   include <memory>


struct program_window : public QMainWindow
{
    program_window(boost::filesystem::path const&  ptree_pathname);
    ~program_window();

    boost::property_tree::ptree&  ptree() { return *m_ptree; }
    qtgl::window<simulator>&  glwindow() noexcept { return m_glwindow; }

public slots:

    void  on_tab_changed(int const  tab_index);

    /// Slots for DRAW tab
    void  on_camera_pos_changed() { m_tab_draw_widgets.on_camera_pos_changed(); }
    void  camera_position_listener() { m_tab_draw_widgets.camera_position_listener(); }
    void  on_camera_rot_changed() { m_tab_draw_widgets.on_camera_rot_changed(); }
    void  on_camera_rot_tait_bryan_changed() { m_tab_draw_widgets.on_camera_rot_tait_bryan_changed(); }
    void  camera_rotation_listener() { m_tab_draw_widgets.camera_rotation_listener(); }
    void  update_camera_rot_widgets(quaternion const&  q) { m_tab_draw_widgets.update_camera_rot_widgets(q); }

    void  on_look_at_selected() { m_tab_draw_widgets.on_look_at_selected(); }

    void  on_camera_far_changed() { m_tab_draw_widgets.on_camera_far_changed(); }
    void  on_camera_speed_changed() { m_tab_draw_widgets.on_camera_speed_changed(); }

    void  on_clear_colour_changed() { m_tab_draw_widgets.on_clear_colour_changed(); }
    void  on_clear_colour_set(QColor const&  colour) { m_tab_draw_widgets.on_clear_colour_set(colour); }
    void  on_clear_colour_choose() { m_tab_draw_widgets.on_clear_colour_choose(); }
    void  on_clear_colour_reset() { m_tab_draw_widgets.on_clear_colour_reset(); }

    void  on_show_grid_changed(int const  value) { m_tab_draw_widgets.on_show_grid_changed(value); }
    void  on_do_render_single_layer_changed(int const  value) { m_tab_draw_widgets.on_do_render_single_layer_changed(value); }
    void  on_layer_index_to_render_changed() { m_tab_draw_widgets.on_layer_index_to_render_changed(); }
    void  on_wrong_index_of_layer_to_render_listener() { m_tab_draw_widgets.on_wrong_index_of_layer_to_render_listener(); }

    void  dbg_on_camera_far_changed() { m_tab_draw_widgets.dbg_on_camera_far_changed(); }
    void  dbg_on_camera_sync_changed(int value) { m_tab_draw_widgets.dbg_on_camera_sync_changed(value); }
    void  dbg_on_frustum_sector_enumeration(int value) { m_tab_draw_widgets.dbg_on_frustum_sector_enumeration(value); }
    void  dbg_on_raycast_sector_enumeration(int value) { m_tab_draw_widgets.dbg_on_raycast_sector_enumeration(value); }
    void  dbg_on_draw_movement_areas(int value) { m_tab_draw_widgets.dbg_on_draw_movement_areas(value); }

    /// Slots for NETWORK tab

    /// Slots for SELECTED tab
    void  on_network_info_text_update()  { m_tab_network_widgets.on_text_update(); }
    void  on_selection_update()  { m_tab_selected_widgets.on_selection_update(); }
    void  on_select_owner_spiker() { m_tab_selected_widgets.on_select_owner_spiker(); }

    /// Slots for PERFORMANCE tab
    void  on_use_update_queues_of_ships_in_network_changed(int const  value)
    { m_tab_performance_widgets.on_use_update_queues_of_ships_in_network_changed(value); }
    void  on_performance_update()  { m_tab_performance_widgets.on_performance_update(); }

    /// Slots for menu actions
    void  on_menu_network_open() { m_menu_bar.on_menu_network_open(); }
    void  on_menu_network_close() { m_menu_bar.on_menu_network_close();  }

private:

    Q_OBJECT

    bool  event(QEvent* const event);
    void  timerEvent(QTimerEvent* const event);
    void  closeEvent(QCloseEvent* const  event);

    boost::filesystem::path  m_ptree_pathname;
    std::unique_ptr<boost::property_tree::ptree>  m_ptree;
    qtgl::window<simulator>  m_glwindow;
    bool  m_has_focus;
    bool  m_focus_just_received;
    int  m_idleTimerId;
    bool  m_is_this_first_timer_event;

    QWidget*  m_gl_window_widget;

    QSplitter*  m_splitter;
    QTabWidget*  m_tabs;

    window_tabs::tab_draw::widgets  m_tab_draw_widgets;
    window_tabs::tab_network::widgets  m_tab_network_widgets;
    window_tabs::tab_selected::widgets  m_tab_selected_widgets;
    window_tabs::tab_performance::widgets  m_tab_performance_widgets;

    menu_bar  m_menu_bar;
    status_bar  m_status_bar;
};


#endif
