set(THIS_TARGET_NAME cpptest)

add_executable(${THIS_TARGET_NAME}
    program_info.hpp
    program_info.cpp

    program_options.hpp
    program_options.cpp

    main.cpp
    run.cpp

    array_of_derived.cpp
    )

target_link_libraries(${THIS_TARGET_NAME}
    utility
    ${BOOST_LIST_OF_LIBRARIES_TO_LINK_WITH}
    )

set_target_properties(${THIS_TARGET_NAME} PROPERTIES
    DEBUG_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Debug"
    RELEASE_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Release"
    )

install(TARGETS ${THIS_TARGET_NAME} DESTINATION "tests")

