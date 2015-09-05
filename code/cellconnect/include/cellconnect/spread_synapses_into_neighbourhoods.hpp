#ifndef CELLCONNECT_SPREAD_SYNAPSES_INTO_NEIGHBOURHOODS_HPP_INCLUDED
#   define CELLCONNECT_SPREAD_SYNAPSES_INTO_NEIGHBOURHOODS_HPP_INCLUDED

#   include <cellconnect/column_shift_function.hpp>
#   include <cellab/dynamic_state_of_neural_tissue.hpp>
#   include <utility/basic_numeric_types.hpp>
#   include <memory>
#   include <vector>

namespace cellconnect {


void  spread_synapses_into_neighbourhoods(
        std::shared_ptr<cellab::dynamic_state_of_neural_tissue> const  dynamic_state_ptr,
        cellab::kind_of_cell const  kind_of_target_cells_of_synapses,
        cellab::kind_of_cell const  kind_of_source_cells_of_synapses,
        natural_32_bit const  diameter_x,
        natural_32_bit const  diameter_y,
        //! A matrix of diameter_x rows and diameter_y columns. Row-axis is aligmend with x-axis of the neural tissue.
        //! The matrix is stored in the vector in the column-major order.
        std::vector<natural_32_bit> const&  matrix_of_counts_of_synapses_to_be_spread_into_columns_in_neighbourhood,
        cellconnect::column_shift_function const&  move_to_target_column,
        natural_32_bit const  num_threads_avalilable_for_computation
        );


}

#endif
