#include <cellab/transition_algorithms.hpp>
#include <cellab/static_state_of_neural_tissue.hpp>
#include <cellab/dynamic_state_of_neural_tissue.hpp>
#include <cellab/shift_in_coordinates.hpp>
#include <cellab/utilities_for_transition_algorithms.hpp>
#include <utility/basic_numeric_types.hpp>
#include <utility/bits_reference.hpp>
#include <utility/assumptions.hpp>
#include <utility/invariants.hpp>
#include <functional>
#include <memory>
#include <vector>
#include <tuple>
#include <thread>

namespace cellab {


static void thread_apply_transition_of_signalling_in_tissue(
        std::shared_ptr<dynamic_state_of_neural_tissue> const dynamic_state_of_tissue,
        std::shared_ptr<static_state_of_neural_tissue const> const static_state_of_tissue,
        single_threaded_in_situ_transition_function_of_packed_dynamic_state_of_signalling const&
            transition_function_of_packed_signalling,
        natural_32_bit x_coord,
        natural_32_bit y_coord,
        natural_32_bit c_coord,
        natural_32_bit const extent_in_coordinates
        )
{
    do
    {
        bits_reference bits_of_signalling =
            dynamic_state_of_tissue->find_bits_of_signalling(x_coord,y_coord,c_coord);

        natural_16_bit const kind_of_territory_cell =
            static_state_of_tissue->compute_kind_of_cell_from_its_position_along_columnar_axis(c_coord);
        INVARIANT(kind_of_territory_cell < static_state_of_tissue->num_kinds_of_tissue_cells());

        tissue_coordinates const territory_cell_coordinates(x_coord,y_coord,c_coord);

        shift_in_coordinates shift_to_low_corner(
            clip_shift(-static_state_of_tissue->get_x_radius_of_cellular_neighbourhood_of_signalling(
                           kind_of_territory_cell),
                       territory_cell_coordinates.get_coord_along_x_axis(),
                       static_state_of_tissue->num_cells_along_x_axis(),
                       static_state_of_tissue->is_x_axis_torus_axis()),
            clip_shift(-static_state_of_tissue->get_y_radius_of_cellular_neighbourhood_of_signalling(
                           kind_of_territory_cell),
                       territory_cell_coordinates.get_coord_along_y_axis(),
                       static_state_of_tissue->num_cells_along_y_axis(),
                       static_state_of_tissue->is_y_axis_torus_axis()),
            clip_shift(-static_state_of_tissue->get_columnar_radius_of_cellular_neighbourhood_of_signalling(
                           kind_of_territory_cell),
                       territory_cell_coordinates.get_coord_along_columnar_axis(),
                       static_state_of_tissue->num_cells_along_columnar_axis(),
                       static_state_of_tissue->is_columnar_axis_torus_axis())
            );

        shift_in_coordinates shift_to_high_corner(
            clip_shift(static_state_of_tissue->get_x_radius_of_cellular_neighbourhood_of_signalling(
                           kind_of_territory_cell),
                       territory_cell_coordinates.get_coord_along_x_axis(),
                       static_state_of_tissue->num_cells_along_x_axis(),
                       static_state_of_tissue->is_x_axis_torus_axis()),
            clip_shift(static_state_of_tissue->get_y_radius_of_cellular_neighbourhood_of_signalling(
                           kind_of_territory_cell),
                       territory_cell_coordinates.get_coord_along_y_axis(),
                       static_state_of_tissue->num_cells_along_y_axis(),
                       static_state_of_tissue->is_y_axis_torus_axis()),
            clip_shift(static_state_of_tissue->get_columnar_radius_of_cellular_neighbourhood_of_signalling(
                           kind_of_territory_cell),
                       territory_cell_coordinates.get_coord_along_columnar_axis(),
                       static_state_of_tissue->num_cells_along_columnar_axis(),
                       static_state_of_tissue->is_columnar_axis_torus_axis())
            );

        spatial_neighbourhood const signalling_neighbourhood(
                    territory_cell_coordinates,shift_to_low_corner,shift_to_high_corner
                    );

        transition_function_of_packed_signalling(
                    bits_of_signalling,
                    kind_of_territory_cell,
                    shift_to_low_corner,
                    shift_to_high_corner,
                    std::bind(&cellab::get_cell_callback_function, dynamic_state_of_tissue,
                              static_state_of_tissue, std::cref(signalling_neighbourhood),
                              std::placeholders::_1)
                    );
    }
    while (go_to_next_coordinates(
                    x_coord,y_coord,c_coord,
                    extent_in_coordinates,
                    static_state_of_tissue->num_cells_along_x_axis(),
                    static_state_of_tissue->num_cells_along_y_axis(),
                    static_state_of_tissue->num_cells_along_columnar_axis()
                    ));
}

void apply_transition_of_signalling_in_tissue(
        std::shared_ptr<dynamic_state_of_neural_tissue> const dynamic_state_of_tissue,
        single_threaded_in_situ_transition_function_of_packed_dynamic_state_of_signalling const&
            transition_function_of_packed_signalling,
        natural_32_bit const  num_threads_avalilable_for_computation
        )
{
    std::shared_ptr<static_state_of_neural_tissue const> const static_state_of_tissue =
            dynamic_state_of_tissue->get_static_state_of_neural_tissue();

    std::vector<std::thread> threads;
    for (natural_32_bit i = 1U; i < num_threads_avalilable_for_computation; ++i)
    {
        natural_32_bit x_coord = 0U;
        natural_32_bit y_coord = 0U;
        natural_32_bit c_coord = 0U;
        if (!go_to_next_coordinates(
                    x_coord,y_coord,c_coord,
                    i,
                    static_state_of_tissue->num_cells_along_x_axis(),
                    static_state_of_tissue->num_cells_along_y_axis(),
                    static_state_of_tissue->num_cells_along_columnar_axis()
                    ))
            break;

        threads.push_back(
                    std::thread(
                        &cellab::thread_apply_transition_of_signalling_in_tissue,
                        dynamic_state_of_tissue,
                        static_state_of_tissue,
                        transition_function_of_packed_signalling,
                        x_coord,y_coord,c_coord,
                        num_threads_avalilable_for_computation
                        )
                    );
    }

    thread_apply_transition_of_signalling_in_tissue(
            dynamic_state_of_tissue,
            static_state_of_tissue,
            transition_function_of_packed_signalling,
            0U,0U,0U,
            num_threads_avalilable_for_computation
            );

    for(std::thread& thread : threads)
        thread.join();
}


}
