#ifndef CELLCONNECT_SPREAD_SYNAPSES_INTO_LOCAL_NEIGHBOURHOODS_HPP_INCLUDED
#   define CELLCONNECT_SPREAD_SYNAPSES_INTO_LOCAL_NEIGHBOURHOODS_HPP_INCLUDED

#   include <cellab/dynamic_state_of_neural_tissue.hpp>
#   include <utility/basic_numeric_types.hpp>
#   include <memory>
#   include <vector>

namespace cellconnect {


void  spread_synapses_into_local_neighbourhoods(
        std::shared_ptr<cellab::dynamic_state_of_neural_tissue> const  dynamic_state_ptr,
        cellab::kind_of_cell const  kind_of_target_cells_of_synapses,
        cellab::kind_of_cell const  kind_of_source_cells_of_synapses,
        natural_32_bit const  diameter_x,
        natural_32_bit const  diameter_y,
        std::vector<natural_32_bit> const&  matrix_of_counts_of_synapses_to_be_spread_into_columns_in_neighbourhood,
        natural_32_bit const  num_threads_avalilable_for_computation
        );


}

#endif
