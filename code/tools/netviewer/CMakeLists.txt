set(THIS_TARGET_NAME netviewer)

set(CMAKE_AUTOMOC ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${QT5_CXX_FLAGS}")

add_executable(${THIS_TARGET_NAME}
    program_info.hpp
    program_info.cpp

    program_options.hpp
    program_options.cpp

    main.cpp
    run.cpp

    simulator.hpp
    simulator.cpp
    simulator_notifications.hpp

    program_window.hpp
    program_window.cpp
    
    window_tabs/tab_draw.hpp
    window_tabs/tab_draw.cpp
    window_tabs/tab_network.hpp
    window_tabs/tab_network.cpp
    window_tabs/tab_selected.hpp
    window_tabs/tab_selected.cpp
    window_tabs/tab_performance.hpp
    window_tabs/tab_performance.cpp

    status_bar.hpp
    status_bar.cpp
    
    menu_bar.hpp
    menu_bar.cpp

    dbg/dbg_network_camera.hpp
    dbg/dbg_network_camera.cpp
    dbg/dbg_frustum_sector_enumeration.hpp
    dbg/dbg_frustum_sector_enumeration.cpp
    dbg/dbg_raycast_sector_enumeration.hpp
    dbg/dbg_raycast_sector_enumeration.cpp
    dbg/dbg_draw_movement_areas.hpp
    dbg/dbg_draw_movement_areas.cpp
    )

target_link_libraries(${THIS_TARGET_NAME}
    netlab
    netexp
    netview
    angeo
    qtgl
    utility
    ${QT5_LIST_OF_LIBRARIES_TO_LINK_WITH}
    ${OPENGL_LIST_OF_LIBRARIES_TO_LINK_WITH}
    ${BOOST_LIST_OF_LIBRARIES_TO_LINK_WITH}
    )

set_target_properties(${THIS_TARGET_NAME} PROPERTIES
    DEBUG_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Debug"
    RELEASE_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Release"
    RELWITHDEBINFO_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_RelWithDebInfo"
    )

install(TARGETS ${THIS_TARGET_NAME} DESTINATION "tools")

