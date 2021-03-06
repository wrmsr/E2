set(THIS_TARGET_NAME view_3d_model)

set(CMAKE_AUTOMOC ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${QT5_CXX_FLAGS}")

add_executable(${THIS_TARGET_NAME}
    program_info.hpp
    program_info.cpp

    program_options.hpp
    program_options.cpp

    main.cpp
    run.cpp

    program_window.hpp
    program_window.cpp

    simulator.hpp
    simulator.cpp

    widgets.hpp
    )

target_link_libraries(${THIS_TARGET_NAME}
    qtgl
    angeo
    utility
    ${BOOST_LIST_OF_LIBRARIES_TO_LINK_WITH}
    ${QT5_LIST_OF_LIBRARIES_TO_LINK_WITH}
    ${OPENGL_LIST_OF_LIBRARIES_TO_LINK_WITH}
    )

set_target_properties(${THIS_TARGET_NAME} PROPERTIES
    DEBUG_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Debug"
    RELEASE_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Release"
    RELWITHDEBINFO_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_RelWithDebInfo"
    )

install(TARGETS ${THIS_TARGET_NAME} DESTINATION "tests")

