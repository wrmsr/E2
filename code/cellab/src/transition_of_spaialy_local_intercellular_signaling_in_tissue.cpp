#include <cellab/dynamic_state_of_neural_tissue.hpp>
#include <utility/basic_numeric_types.hpp>
#include <utility/bits_reference.hpp>
#include <functional>
#include <memory>
#include <vector>

#include <utility/development.hpp>

namespace cellab {


void apply_transition_of_spaialy_local_intercellular_signaling_in_tissue(
        std::shared_ptr<dynamic_state_of_neural_tissue const> const dynamic_state_of_tissue,
        std::function<
            void(
            bits_reference bits_of_signaling_data_to_be_updated,
            std::vector<bits_const_reference> const& bits_of_all_cells_in_neighbourhood,
            )> transition_function_of_local_intercellular_signaling,
        natural_32_bit num_avalilable_thread_for_creation_and_use
        )
{
    NOT_IMPLEMENTED_YET();
}


}
