set(THIS_TARGET_NAME cellconnect)

add_library(${THIS_TARGET_NAME}
    ./include/cellconnect/fill_coords_of_source_cells_of_synapses_in_tissue.hpp
    ./src/fill_coords_of_source_cells_of_synapses_in_tissue.cpp

    ./include/cellconnect/fill_delimiters_between_territorial_lists.hpp
    ./src/fill_delimiters_between_territorial_lists.cpp

    ./include/cellconnect/spread_synapses_into_neighbourhoods.hpp
    ./src/spread_synapses_into_neighbourhoods.cpp

    ./include/cellconnect/column_shift_function.hpp
    ./src/column_shift_function.cpp

    ./include/cellconnect/check_for_network_properties.hpp
    ./src/check_for_network_properties.cpp
    ./src/compute_in_degrees.cpp
    ./src/compute_out_degrees.cpp

    ./include/cellconnect/dump.hpp
    ./src/dump.cpp
    )

set_target_properties(${THIS_TARGET_NAME} PROPERTIES
    DEBUG_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Debug"
    RELEASE_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Release"
    RELWITHDEBINFO_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_RelWithDebInfo"
    )

install(TARGETS ${THIS_TARGET_NAME} DESTINATION "lib")
