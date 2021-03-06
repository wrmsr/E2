#include "./program_window.hpp"
#include "./program_info.hpp"
#include "./simulator.hpp"
#include <qtgl/window.hpp>
#include <qtgl/gui_utils.hpp>
#include <qtgl/widget_base.hpp>
#include <utility/msgstream.hpp>
#include <boost/filesystem.hpp>
#include <boost/property_tree/info_parser.hpp>
#include <QString>
#include <QIntValidator>
#include <QDoubleValidator>
#include <QIcon>
#include <QStatusBar>
#include <QLabel>
#include <QColorDialog>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGroupBox>
#include <QPushButton>
#include <iomanip>


namespace tab_names { namespace {


inline std::string  CAMERA() noexcept { return "Camera"; }
inline std::string  DRAW() noexcept { return "Draw"; }
inline std::string  NENET() noexcept { return "Nenet"; }
inline std::string  SELECTED() noexcept { return "Selected"; }


}}

namespace {


std::unique_ptr<boost::property_tree::ptree>  load_ptree(boost::filesystem::path const&  ptree_pathname)
{
    std::unique_ptr<boost::property_tree::ptree>  ptree(new boost::property_tree::ptree);
    if (boost::filesystem::exists(ptree_pathname))
        boost::property_tree::read_info(ptree_pathname.string(), *ptree);
    return std::move(ptree);
}


}


program_window::program_window(boost::filesystem::path const&  ptree_pathname)
    : QMainWindow(nullptr)
    , m_ptree_pathname(ptree_pathname)
    , m_ptree(load_ptree(m_ptree_pathname))
    , m_glwindow(vector3(m_ptree->get("tabs.draw.clear_colour.red", 64) / 255.0f,
                         m_ptree->get("tabs.draw.clear_colour.green", 64) / 255.0f,
                         m_ptree->get("tabs.draw.clear_colour.blue", 64) / 255.0f),
                 m_ptree->get("nenet.simulation.paused", false),
                 std::make_shared<nenet::params>(
                     m_ptree->get("nenet.params.time_step", 0.001f),
                     m_ptree->get("nenet.params.mini_spiking_potential_magnitude", 0.075f),
                     m_ptree->get("nenet.params.average_mini_spiking_period_in_seconds", 10.0f / 1000.0f),
                     m_ptree->get("nenet.params.spiking_potential_magnitude", 0.4f),
                     m_ptree->get("nenet.params.resting_potential", 0.0f),
                     m_ptree->get("nenet.params.spiking_threshold", 1.0f),
                     m_ptree->get("nenet.params.after_spike_potential", -1.0f),
                     m_ptree->get("nenet.params.potential_descend_coef", 0.2f),
                     m_ptree->get("nenet.params.potential_ascend_coef", 0.01f),
                     m_ptree->get("nenet.params.max_connection_distance", 0.25f),
                     m_ptree->get("nenet.params.output_terminal_velocity_max_magnitude", 0.01f),
                     m_ptree->get("nenet.params.output_terminal_velocity_min_magnitude", 0.003f)
                     ),
                 m_ptree->get("nenet.params.speed", 1.0f)
                 )
    , m_has_focus(false)
    , m_focus_just_received(true)
    , m_idleTimerId(-1)

    , m_gl_window_widget(m_glwindow.create_widget_container())

    , m_splitter(new QSplitter(Qt::Horizontal, this))
    , m_tabs(
        [](program_window* wnd) {
            struct s : public QTabWidget {
                s(program_window* wnd) : QTabWidget()
                {
                    connect(this, SIGNAL(currentChanged(int)), wnd, SLOT(on_tab_changed(int)));
                }
            };
            return new s(wnd);
        }(this)
        )

    , m_clear_colour_component_red(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setValidator(new QIntValidator(0, 255));
                    setText(QString::number(wnd->ptree().get("tabs.draw.clear_colour.red", 64)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_clear_colour_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_clear_colour_component_green(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setValidator(new QIntValidator(0, 255));
                    setText(QString::number(wnd->ptree().get("tabs.draw.clear_colour.green", 64)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_clear_colour_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_clear_colour_component_blue(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setValidator(new QIntValidator(0, 255));
                    setText(QString::number(wnd->ptree().get("tabs.draw.clear_colour.blue", 64)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_clear_colour_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )

    , m_camera_pos_x(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("tabs.camera.pos.x", 0.5f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_pos_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_camera_pos_y(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("tabs.camera.pos.y", 0.5f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_pos_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_camera_pos_z(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("tabs.camera.pos.z", 2.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_pos_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )

    , m_camera_rot_w(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("tabs.camera.rot.w", 1.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_rot_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_camera_rot_x(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("tabs.camera.rot.x", 0.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_rot_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_camera_rot_y(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("tabs.camera.rot.y", 0.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_rot_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_camera_rot_z(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("tabs.camera.rot.z", 0.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_rot_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )

    , m_camera_yaw(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_rot_tait_bryan_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_camera_pitch(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_rot_tait_bryan_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_camera_roll(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_camera_rot_tait_bryan_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )

    , m_camera_save_pos_rot(new QCheckBox("Save position and rotation"))


    , m_nenet_param_time_step(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.time_step", 0.001f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_time_step_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_simulation_speed(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.speed", 1.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_simulation_speed_changed()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_mini_spiking_potential_magnitude(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.mini_spiking_potential_magnitude", 0.075f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_mini_spiking_potential_magnitude()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_average_mini_spiking_period_in_seconds(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.m_nenet_param_average_mini_spiking_period_in_seconds", 10.0f / 1000.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_average_mini_spiking_period_in_seconds()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_spiking_potential_magnitude(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.spiking_potential_magnitude", 0.4f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_spiking_potential_magnitude()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_resting_potential(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.resting_potential", 0.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_resting_potential()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_spiking_threshold(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.spiking_threshold", 1.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_spiking_threshold()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_after_spike_potential(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.after_spike_potential", -1.0f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_after_spike_potential()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_potential_descend_coef(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.potential_descend_coef", 0.2f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_potential_descend_coef()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_potential_ascend_coef(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.potential_ascend_coef", 0.01f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_potential_ascend_coef()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_max_connection_distance(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.max_connection_distance", 0.25f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_max_connection_distance()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_output_terminal_velocity_max_magnitude(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.output_terminal_velocity_max_magnitude", 0.01f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_output_terminal_velocity_max_magnitude()));
                }
            };
            return new s(wnd);
        }(this)
        )
    , m_nenet_param_output_terminal_velocity_min_magnitude(
        [](program_window* wnd) {
            struct s : public QLineEdit {
                s(program_window* wnd) : QLineEdit()
                {
                    setText(QString::number(wnd->ptree().get("nenet.params.output_terminal_velocity_min_magnitude", 0.003f)));
                    QObject::connect(this, SIGNAL(editingFinished()), wnd, SLOT(on_nenet_param_output_terminal_velocity_min_magnitude()));
                }
            };
            return new s(wnd);
        }(this)
        )

    , m_selected_props(new QTextEdit)

    , m_spent_real_time(new QLabel("0.0s"))
    , m_spent_simulation_time(new QLabel("0.0s"))
    , m_spent_times_ratio(new QLabel("1.0"))
    , m_num_passed_simulation_steps(new QLabel("#Steps: 0"))
{
    this->setWindowTitle(get_program_name().c_str());
    this->setWindowIcon(QIcon("../data/shared/gfx/icons/E2_icon.png"));
    this->move({ ptree().get("program_window.pos.x",0),ptree().get("program_window.pos.y",0) });
    this->resize(ptree().get("program_window.width", 1024), ptree().get("program_window.height", 768));

    this->setCentralWidget(m_splitter);
    m_splitter->addWidget(m_gl_window_widget);
    m_splitter->addWidget(m_tabs);

    // Building Camera tab
    {
        QWidget* const  camera_tab = new QWidget;
        {
            QVBoxLayout* const camera_tab_layout = new QVBoxLayout;
            {
                QWidget* const position_group = new QGroupBox("Position in meters [xyz]");
                {
                    QHBoxLayout* const position_layout = new QHBoxLayout;
                    {
                        position_layout->addWidget(m_camera_pos_x);
                        position_layout->addWidget(m_camera_pos_y);
                        position_layout->addWidget(m_camera_pos_z);
                        on_camera_pos_changed();
                        m_glwindow.register_listener(notifications::camera_position_updated(),
                        { &program_window::camera_position_listener,this });
                    }
                    position_group->setLayout(position_layout);
                }
                camera_tab_layout->addWidget(position_group);

                QWidget* const rotation_group = new QGroupBox("Rotation");
                {
                    QVBoxLayout* const rotation_layout = new QVBoxLayout;
                    {
                        rotation_layout->addWidget(new QLabel("Quaternion [wxyz]"));
                        QHBoxLayout* const quaternion_layout = new QHBoxLayout;
                        {
                            quaternion_layout->addWidget(m_camera_rot_w);
                            quaternion_layout->addWidget(m_camera_rot_x);
                            quaternion_layout->addWidget(m_camera_rot_y);
                            quaternion_layout->addWidget(m_camera_rot_z);
                        }
                        rotation_layout->addLayout(quaternion_layout);

                        rotation_layout->addWidget(new QLabel("Tait-Bryan angles in degrees [yaw(z)-pitch(y')-roll(x'')]"));
                        QHBoxLayout* const tait_bryan_layout = new QHBoxLayout;
                        {
                            tait_bryan_layout->addWidget(m_camera_yaw);
                            tait_bryan_layout->addWidget(m_camera_pitch);
                            tait_bryan_layout->addWidget(m_camera_roll);
                        }
                        rotation_layout->addLayout(tait_bryan_layout);
                    }
                    rotation_group->setLayout(rotation_layout);

                    on_camera_rot_changed();
                    m_glwindow.register_listener(notifications::camera_orientation_updated(),
                    { &program_window::camera_rotation_listener,this });
                }
                camera_tab_layout->addWidget(rotation_group);

                m_camera_save_pos_rot->setCheckState(
                    ptree().get("tabs.camera.save_pos_rot", true) ? Qt::CheckState::Checked :
                    Qt::CheckState::Unchecked
                    );
                camera_tab_layout->addWidget(m_camera_save_pos_rot);

                camera_tab_layout->addStretch(1);
            }
            camera_tab->setLayout(camera_tab_layout);
        }
        m_tabs->addTab(camera_tab, QString(tab_names::CAMERA().c_str()));
    }

    // Building Draw tab
    {
        QWidget* const  draw_tab = new QWidget;
        {
            QVBoxLayout* const draw_tab_layout = new QVBoxLayout;
            {
                QWidget* const clear_colour_group = new QGroupBox("Clear colour [rgb]");
                {
                    QVBoxLayout* const clear_colour_layout = new QVBoxLayout;
                    {
                        QHBoxLayout* const edit_boxes_layout = new QHBoxLayout;
                        {
                            edit_boxes_layout->addWidget(m_clear_colour_component_red);
                            edit_boxes_layout->addWidget(m_clear_colour_component_green);
                            edit_boxes_layout->addWidget(m_clear_colour_component_blue);
                            on_clear_colour_changed();
                        }
                        clear_colour_layout->addLayout(edit_boxes_layout);

                        QHBoxLayout* const buttons_layout = new QHBoxLayout;
                        {
                            buttons_layout->addWidget(
                                [](program_window* wnd) {
                                struct choose : public QPushButton {
                                    choose(program_window* wnd) : QPushButton("Choose")
                                    {
                                        QObject::connect(this, SIGNAL(released()), wnd, SLOT(on_clear_colour_choose()));
                                    }
                                };
                                return new choose(wnd);
                            }(this)
                                );
                            buttons_layout->addWidget(
                                [](program_window* wnd) {
                                struct choose : public QPushButton {
                                    choose(program_window* wnd) : QPushButton("Default")
                                    {
                                        QObject::connect(this, SIGNAL(released()), wnd, SLOT(on_clear_colour_reset()));
                                    }
                                };
                                return new choose(wnd);
                            }(this)
                                );
                        }
                        clear_colour_layout->addLayout(buttons_layout);

                    }
                    clear_colour_group->setLayout(clear_colour_layout);
                }
                draw_tab_layout->addWidget(clear_colour_group);
                draw_tab_layout->addStretch(1);
            }
            draw_tab->setLayout(draw_tab_layout);
        }
        m_tabs->addTab(draw_tab, QString(tab_names::DRAW().c_str()));
    }

    // Building Nenet tab
    {
        QWidget* const  nenet_tab = new QWidget;
        {
            QVBoxLayout* const nenet_tab_layout = new QVBoxLayout;
            {
                QHBoxLayout* const time_step_layout = new QHBoxLayout;
                {
                    time_step_layout->addWidget(new QLabel("Time step in seconds:"));
                    time_step_layout->addWidget(m_nenet_param_time_step);
                }
                nenet_tab_layout->addLayout(time_step_layout);
                time_step_layout->addStretch(1);

                QHBoxLayout* const speed_layout = new QHBoxLayout;
                {
                    speed_layout->addWidget(new QLabel("Number of simulated seconds per second:"));
                    speed_layout->addWidget(m_nenet_param_simulation_speed);
                }
                nenet_tab_layout->addLayout(speed_layout);
                speed_layout->addStretch(1);

                QHBoxLayout* const mini_spiking_potential_magnitude_layout = new QHBoxLayout;
                {
                    mini_spiking_potential_magnitude_layout->addWidget(new QLabel("Mini spiking potential magnitude:"));
                    mini_spiking_potential_magnitude_layout->addWidget(m_nenet_param_mini_spiking_potential_magnitude);
                }
                nenet_tab_layout->addLayout(mini_spiking_potential_magnitude_layout);
                mini_spiking_potential_magnitude_layout->addStretch(1);

                QHBoxLayout* const average_mini_spiking_period_in_seconds_layout = new QHBoxLayout;
                {
                    average_mini_spiking_period_in_seconds_layout->addWidget(new QLabel("Average mini spiking period in seconds:"));
                    average_mini_spiking_period_in_seconds_layout->addWidget(m_nenet_param_average_mini_spiking_period_in_seconds);
                }
                nenet_tab_layout->addLayout(average_mini_spiking_period_in_seconds_layout);
                average_mini_spiking_period_in_seconds_layout->addStretch(1);

                QHBoxLayout* const spiking_potential_magnitude_layout = new QHBoxLayout;
                {
                    spiking_potential_magnitude_layout->addWidget(new QLabel("Spiking potential magnitude:"));
                    spiking_potential_magnitude_layout->addWidget(m_nenet_param_spiking_potential_magnitude);
                }
                nenet_tab_layout->addLayout(spiking_potential_magnitude_layout);
                spiking_potential_magnitude_layout->addStretch(1);

                QHBoxLayout* const resting_potential_layout = new QHBoxLayout;
                {
                    resting_potential_layout->addWidget(new QLabel("Resting potential:"));
                    resting_potential_layout->addWidget(m_nenet_param_resting_potential);
                }
                nenet_tab_layout->addLayout(resting_potential_layout);
                resting_potential_layout->addStretch(1);

                QHBoxLayout* const after_spike_potential_layout = new QHBoxLayout;
                {
                    after_spike_potential_layout->addWidget(new QLabel("After spike potential:"));
                    after_spike_potential_layout->addWidget(m_nenet_param_after_spike_potential);
                }
                nenet_tab_layout->addLayout(after_spike_potential_layout);
                after_spike_potential_layout->addStretch(1);

                QHBoxLayout* const potential_descend_coef_layout = new QHBoxLayout;
                {
                    potential_descend_coef_layout->addWidget(new QLabel("Potential descend coef:"));
                    potential_descend_coef_layout->addWidget(m_nenet_param_potential_descend_coef);
                }
                nenet_tab_layout->addLayout(potential_descend_coef_layout);
                potential_descend_coef_layout->addStretch(1);

                QHBoxLayout* const potential_ascend_coef_layout = new QHBoxLayout;
                {
                    potential_ascend_coef_layout->addWidget(new QLabel("Potential ascend coef:"));
                    potential_ascend_coef_layout->addWidget(m_nenet_param_potential_ascend_coef);
                }
                nenet_tab_layout->addLayout(potential_ascend_coef_layout);
                potential_ascend_coef_layout->addStretch(1);

                QHBoxLayout* const max_connection_distance_layout = new QHBoxLayout;
                {
                    max_connection_distance_layout->addWidget(new QLabel("Max connection distance:"));
                    max_connection_distance_layout->addWidget(m_nenet_param_max_connection_distance);
                }
                nenet_tab_layout->addLayout(max_connection_distance_layout);
                max_connection_distance_layout->addStretch(1);

                QHBoxLayout* const output_terminal_velocity_max_magnitude_layout = new QHBoxLayout;
                {
                    output_terminal_velocity_max_magnitude_layout->addWidget(new QLabel("Output terminal velocity max magnitude:"));
                    output_terminal_velocity_max_magnitude_layout->addWidget(m_nenet_param_output_terminal_velocity_max_magnitude);
                }
                nenet_tab_layout->addLayout(output_terminal_velocity_max_magnitude_layout);
                output_terminal_velocity_max_magnitude_layout->addStretch(1);

                QHBoxLayout* const output_terminal_velocity_min_magnitude_layout = new QHBoxLayout;
                {
                    output_terminal_velocity_min_magnitude_layout->addWidget(new QLabel("Output terminal velocity min magnitude:"));
                    output_terminal_velocity_min_magnitude_layout->addWidget(m_nenet_param_output_terminal_velocity_min_magnitude);
                }
                nenet_tab_layout->addLayout(output_terminal_velocity_min_magnitude_layout);
                output_terminal_velocity_min_magnitude_layout->addStretch(1);

            }
            nenet_tab->setLayout(nenet_tab_layout);
            nenet_tab_layout->addStretch(1);
        }
        m_tabs->addTab(nenet_tab, QString(tab_names::NENET().c_str()));
    }

    // Building Selected tab
    {
        QWidget* const  selected_tab = new QWidget;
        {
            QVBoxLayout* const layout = new QVBoxLayout;
            {
                m_selected_props->setReadOnly(true);
                layout->addWidget(m_selected_props);
            }
            selected_tab->setLayout(layout);
            //layout->addStretch(1);
        }
        m_tabs->addTab(selected_tab, QString(tab_names::SELECTED().c_str()));
        m_glwindow.register_listener(notifications::selection_changed(), { &program_window::on_selection_changed,this });
    }

    statusBar()->addPermanentWidget(m_spent_real_time);
    statusBar()->addPermanentWidget(m_spent_simulation_time);
    statusBar()->addPermanentWidget(m_spent_times_ratio);
    statusBar()->addPermanentWidget(m_num_passed_simulation_steps);
    statusBar()->addPermanentWidget(
            [](qtgl::window<simulator>* const glwindow, bool const  paused) {
                struct s : public qtgl::widget_base<s, qtgl::window<simulator> >, public QLabel {
                    s(qtgl::window<simulator>* const  glwindow, bool const  paused)
                        : qtgl::widget_base<s, qtgl::window<simulator> >(glwindow), QLabel()
                    {
                        setText(paused ? "PAUSED" : "RUNNING");
                        register_listener(notifications::paused(),&s::on_paused_changed);
                    }
                    void  on_paused_changed()
                    {
                        setText(call_now(&simulator::paused) ? "PAUSED" : "RUNNING");
                    }
                };
                return new s(glwindow, paused);
            }(&m_glwindow, m_ptree->get("nenet.simulation.paused", false))
            );
    statusBar()->addPermanentWidget(
            [](qtgl::window<simulator>* const glwindow) {
                struct s : public qtgl::widget_base<s, qtgl::window<simulator> >, public QLabel {
                    s(qtgl::window<simulator>* const  glwindow)
                        : qtgl::widget_base<s, qtgl::window<simulator> >(glwindow), QLabel()
                    {
                        setText("FPS: 0");
                        register_listener(qtgl::notifications::fps_updated(),
                            &s::on_fps_changed);
                    }
                    void  on_fps_changed()
                    {
                        std::stringstream  sstr;
                        sstr << "FPS: " << call_now(&qtgl::real_time_simulator::FPS);
                        setText(sstr.str().c_str());
                    }
                };
                return new s(glwindow);
            }(&m_glwindow)
            );
    statusBar()->showMessage("Ready", 2000);

    if (ptree().get("program_window.show_maximised", false))
        this->showMaximized();
    else
        this->show();

    qtgl::set_splitter_sizes(*m_splitter, ptree().get("program_window.splitter_ratio", 3.0f / 4.0f));

    //m_gl_window_widget->setFocus();

    m_idleTimerId = startTimer(100); // In milliseconds.
}

program_window::~program_window()
{
}

bool program_window::event(QEvent* const event)
{
    switch (event->type())
    {
    case QEvent::WindowActivate:
    case QEvent::FocusIn:
        m_has_focus = true;
        m_focus_just_received = true;
        return QMainWindow::event(event);
    case QEvent::WindowDeactivate:
    case QEvent::FocusOut:
        m_has_focus = false;
        return QMainWindow::event(event);
    default:
        return QMainWindow::event(event);
    }
}

void program_window::timerEvent(QTimerEvent* const event)
{
    if (event->timerId() != m_idleTimerId)
        return;

    // Here put time-dependent updates...

    {
        float_64_bit const  real_time = m_glwindow.call_now(&simulator::spent_real_time);
        std::string  msg = msgstream() << "RT: " << std::fixed << std::setprecision(3) << real_time << "s";
        m_spent_real_time->setText(msg.c_str());

        float_64_bit const  simulation_time = m_glwindow.call_now(&simulator::spent_simulation_time);
        msg = msgstream() << "ST: " << std::fixed << std::setprecision(3) << simulation_time  << "s";
        m_spent_simulation_time->setText(msg.c_str());

        float_64_bit const  simulation_time_to_real_time = real_time > 1e-5f ? simulation_time / real_time : 1.0;
        msg = msgstream() << "ST/RT: " << std::fixed << std::setprecision(3) << simulation_time_to_real_time;
        m_spent_times_ratio->setText(msg.c_str());

        natural_64_bit const  num_steps = m_glwindow.call_now(&simulator::nenet_num_updates);
        msg = msgstream() << "#Steps: " << num_steps;
        m_num_passed_simulation_steps->setText(msg.c_str());
    }

    if (qtgl::to_string(m_tabs->tabText(m_tabs->currentIndex())) == tab_names::SELECTED())
        on_selection_changed();

    if (m_focus_just_received)
    {
        m_focus_just_received = false;
        m_gl_window_widget->setFocus();
    }
}

void  program_window::closeEvent(QCloseEvent* const  event)
{
    ptree().put("program_window.pos.x", pos().x());
    ptree().put("program_window.pos.y", pos().y());
    ptree().put("program_window.width", width());
    ptree().put("program_window.height", height());
    ptree().put("program_window.splitter_ratio", qtgl::get_splitter_sizes_ratio(*m_splitter));
    ptree().put("program_window.show_maximised", isMaximized());

    ptree().put("tabs.draw.clear_colour.red", m_clear_colour_component_red->text().toInt());
    ptree().put("tabs.draw.clear_colour.green", m_clear_colour_component_green->text().toInt());
    ptree().put("tabs.draw.clear_colour.blue", m_clear_colour_component_blue->text().toInt());

    if (m_camera_save_pos_rot->isChecked())
    {
        ptree().put("tabs.camera.pos.x", m_camera_pos_x->text().toFloat());
        ptree().put("tabs.camera.pos.y", m_camera_pos_y->text().toFloat());
        ptree().put("tabs.camera.pos.z", m_camera_pos_z->text().toFloat());
        ptree().put("tabs.camera.rot.w", m_camera_rot_w->text().toFloat());
        ptree().put("tabs.camera.rot.x", m_camera_rot_x->text().toFloat());
        ptree().put("tabs.camera.rot.y", m_camera_rot_y->text().toFloat());
        ptree().put("tabs.camera.rot.z", m_camera_rot_z->text().toFloat());
    }
    ptree().put("tabs.camera.save_pos_rot", m_camera_save_pos_rot->isChecked());

    ptree().put("nenet.simulation.paused", m_glwindow.call_now(&simulator::paused));

    ptree().put("nenet.params.time_step", m_glwindow.call_now(&simulator::update_time_step_in_seconds));
    ptree().put("nenet.params.speed", m_glwindow.call_now(&simulator::desired_number_of_simulated_seconds_per_real_time_second));
    ptree().put("nenet.params.mini_spiking_potential_magnitude", m_glwindow.call_now(&simulator::mini_spiking_potential_magnitude));
    ptree().put("nenet.params.average_mini_spiking_period_in_seconds", m_glwindow.call_now(&simulator::average_mini_spiking_period_in_seconds));
    ptree().put("nenet.params.spiking_potential_magnitude", m_glwindow.call_now(&simulator::spiking_potential_magnitude));
    ptree().put("nenet.params.resting_potential", m_glwindow.call_now(&simulator::resting_potential));
    ptree().put("nenet.params.spiking_threshold", m_glwindow.call_now(&simulator::spiking_threshold));
    ptree().put("nenet.params.after_spike_potential", m_glwindow.call_now(&simulator::after_spike_potential));
    ptree().put("nenet.params.potential_descend_coef", m_glwindow.call_now(&simulator::potential_descend_coef));
    ptree().put("nenet.params.potential_ascend_coef", m_glwindow.call_now(&simulator::potential_ascend_coef));
    ptree().put("nenet.params.max_connection_distance", m_glwindow.call_now(&simulator::max_connection_distance));
    ptree().put("nenet.params.output_terminal_velocity_max_magnitude", m_glwindow.call_now(&simulator::output_terminal_velocity_max_magnitude));
    ptree().put("nenet.params.output_terminal_velocity_min_magnitude", m_glwindow.call_now(&simulator::output_terminal_velocity_min_magnitude));

    boost::property_tree::write_info(m_ptree_pathname.string(), ptree());
}

void  program_window::on_tab_changed(int const  tab_index)
{
    std::string const  tab_name = qtgl::to_string(m_tabs->tabText(tab_index));
    if (tab_name == tab_names::CAMERA())
    {
        // Nothing to do...
    }
    else if (tab_name == tab_names::DRAW())
    {
        // Nothing to do...
    }
    else if (tab_name == tab_names::SELECTED())
    {
        on_selection_changed();
    }
}

void program_window::on_clear_colour_changed()
{
    vector3 const  colour(
        (float_32_bit)m_clear_colour_component_red->text().toInt() / 255.0f,
        (float_32_bit)m_clear_colour_component_green->text().toInt() / 255.0f,
        (float_32_bit)m_clear_colour_component_blue->text().toInt() / 255.0f
        );
    m_glwindow.call_later(&simulator::set_clear_color, colour);
}

void program_window::on_clear_colour_set(QColor const&  colour)
{
    m_clear_colour_component_red->setText(QString::number(colour.red()));
    m_clear_colour_component_green->setText(QString::number(colour.green()));
    m_clear_colour_component_blue->setText(QString::number(colour.blue()));
    on_clear_colour_changed();
}

void program_window::on_clear_colour_choose()
{
    QColor const  init_colour(m_clear_colour_component_red->text().toInt(),
        m_clear_colour_component_green->text().toInt(),
        m_clear_colour_component_blue->text().toInt());
    QColor const  colour = QColorDialog::getColor(init_colour, this, "Choose clear colour");
    if (!colour.isValid())
        return;
    on_clear_colour_set(colour);
}

void program_window::on_clear_colour_reset()
{
    on_clear_colour_set(QColor(64, 64, 64));
}

void  program_window::on_camera_pos_changed()
{
    vector3 const  pos(m_camera_pos_x->text().toFloat(),
        m_camera_pos_y->text().toFloat(),
        m_camera_pos_z->text().toFloat());
    m_glwindow.call_later(&simulator::set_camera_position, pos);
}

void  program_window::camera_position_listener()
{
    vector3 const pos = m_glwindow.call_now(&simulator::get_camera_position);
    m_camera_pos_x->setText(QString::number(pos(0)));
    m_camera_pos_y->setText(QString::number(pos(1)));
    m_camera_pos_z->setText(QString::number(pos(2)));
}

void  program_window::on_camera_rot_changed()
{
    quaternion  q(m_camera_rot_w->text().toFloat(),
        m_camera_rot_x->text().toFloat(),
        m_camera_rot_y->text().toFloat(),
        m_camera_rot_z->text().toFloat());
    if (length_squared(q) < 1e-5f)
        q.z() = 1.0f;
    normalise(q);

    update_camera_rot_widgets(q);
    m_glwindow.call_later(&simulator::set_camera_orientation, q);
}

void  program_window::on_camera_rot_tait_bryan_changed()
{
    quaternion  q = rotation_matrix_to_quaternion(yaw_pitch_roll_to_rotation(
        m_camera_yaw->text().toFloat() * PI() / 180.0f,
        m_camera_pitch->text().toFloat() * PI() / 180.0f,
        m_camera_roll->text().toFloat() * PI() / 180.0f
        ));
    normalise(q);
    update_camera_rot_widgets(q);
    m_glwindow.call_later(&simulator::set_camera_orientation, q);
}

void  program_window::camera_rotation_listener()
{
    update_camera_rot_widgets(m_glwindow.call_now(&simulator::get_camera_orientation));
}

void  program_window::update_camera_rot_widgets(quaternion const&  q)
{
    m_camera_rot_w->setText(QString::number(q.w()));
    m_camera_rot_x->setText(QString::number(q.x()));
    m_camera_rot_y->setText(QString::number(q.y()));
    m_camera_rot_z->setText(QString::number(q.z()));

    scalar  yaw, pitch, roll;
    rotation_to_yaw_pitch_roll(quaternion_to_rotation_matrix(q), yaw, pitch, roll);
    m_camera_yaw->setText(QString::number(yaw * 180.0f / PI()));
    m_camera_pitch->setText(QString::number(pitch * 180.0f / PI()));
    m_camera_roll->setText(QString::number(roll * 180.0f / PI()));
}

void  program_window::on_nenet_param_simulation_speed_changed()
{
    m_glwindow.call_later(&simulator::set_desired_number_of_simulated_seconds_per_real_time_second, m_nenet_param_simulation_speed->text().toFloat());
}

void  program_window::on_nenet_param_time_step_changed()
{
    m_glwindow.call_later(&simulator::set_update_time_step_in_seconds, m_nenet_param_time_step->text().toFloat());
}

void  program_window::on_nenet_param_mini_spiking_potential_magnitude()
{
    m_glwindow.call_later(&simulator::set_mini_spiking_potential_magnitude, m_nenet_param_mini_spiking_potential_magnitude->text().toFloat());
}

void  program_window::on_nenet_param_average_mini_spiking_period_in_seconds()
{
    m_glwindow.call_later(&simulator::set_average_mini_spiking_period_in_seconds, m_nenet_param_average_mini_spiking_period_in_seconds->text().toFloat());
}

void  program_window::on_nenet_param_spiking_potential_magnitude()
{
    m_glwindow.call_later(&simulator::set_spiking_potential_magnitude, m_nenet_param_spiking_potential_magnitude->text().toFloat());
}

void  program_window::on_nenet_param_resting_potential()
{
    m_glwindow.call_later(&simulator::set_resting_potential, m_nenet_param_resting_potential->text().toFloat());
}

void  program_window::on_nenet_param_spiking_threshold()
{
    m_glwindow.call_later(&simulator::set_spiking_threshold, m_nenet_param_spiking_threshold->text().toFloat());
}

void  program_window::on_nenet_param_after_spike_potential()
{
    m_glwindow.call_later(&simulator::set_after_spike_potential, m_nenet_param_after_spike_potential->text().toFloat());
}

void  program_window::on_nenet_param_potential_descend_coef()
{
    m_glwindow.call_later(&simulator::set_potential_descend_coef, m_nenet_param_potential_descend_coef->text().toFloat());
}

void  program_window::on_nenet_param_potential_ascend_coef()
{
    m_glwindow.call_later(&simulator::set_potential_ascend_coef, m_nenet_param_potential_ascend_coef->text().toFloat());
}

void  program_window::on_nenet_param_max_connection_distance()
{
    m_glwindow.call_later(&simulator::set_max_connection_distance, m_nenet_param_max_connection_distance->text().toFloat());
}

void  program_window::on_nenet_param_output_terminal_velocity_max_magnitude()
{
    m_glwindow.call_later(&simulator::set_output_terminal_velocity_max_magnitude, m_nenet_param_output_terminal_velocity_max_magnitude->text().toFloat());
}

void  program_window::on_nenet_param_output_terminal_velocity_min_magnitude()
{
    m_glwindow.call_later(&simulator::set_output_terminal_velocity_min_magnitude, m_nenet_param_output_terminal_velocity_min_magnitude->text().toFloat());
}

void program_window::on_selection_changed()
{
    std::string const  text = m_glwindow.call_now(&simulator::get_selected_info_text);
    m_selected_props->setText(QString(text.c_str()));
}
