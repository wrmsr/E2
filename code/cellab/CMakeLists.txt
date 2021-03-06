set(THIS_TARGET_NAME cellab)

add_library(${THIS_TARGET_NAME}
    ./include/cellab/static_state_of_neural_tissue.hpp
    ./src/static_state_of_neural_tissue.cpp

    ./include/cellab/dynamic_state_of_neural_tissue.hpp
    ./src/dynamic_state_of_neural_tissue.cpp

    ./include/cellab/territorial_state_of_synapse.hpp
    ./src/territorial_state_of_synapse.cpp

    ./include/cellab/shift_in_coordinates.hpp
    ./src/shift_in_coordinates.cpp

    ./include/cellab/homogenous_slice_of_tissue.hpp
    ./src/homogenous_slice_of_tissue.cpp

    ./include/cellab/transition_algorithms.hpp
    ./src/transition_of_synapses_to_muscles.cpp
    ./src/transition_of_synapses_of_tissue.cpp
    ./src/transition_of_territorial_lists_of_synapses.cpp
    ./src/transition_of_synaptic_migration_in_tissue.cpp
    ./src/transition_of_signalling_in_tissue.cpp
    ./src/transition_of_cells_of_tissue.cpp

    ./include/cellab/utilities_for_transition_algorithms.hpp
    ./src/utilities_for_transition_algorithms.cpp

    ./include/cellab/neural_tissue.hpp
    ./src/neural_tissue.cpp

    ./include/cellab/utilities_for_construction_of_neural_tissue.hpp

    ./include/cellab/dump.hpp
    ./src/dump.cpp
    )

set_target_properties(${THIS_TARGET_NAME} PROPERTIES
    DEBUG_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Debug"
    RELEASE_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Release"
    RELWITHDEBINFO_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_RelWithDebInfo"
    )

install(TARGETS ${THIS_TARGET_NAME} DESTINATION "lib")
