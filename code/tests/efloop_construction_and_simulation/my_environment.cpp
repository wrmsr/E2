#include "./my_environment.hpp"
#include "./my_cell.hpp"
#include "./my_synapse.hpp"
#include "./my_signalling.hpp"
#include <cellab/utilities_for_transition_algorithms.hpp>
#include <utility/random.hpp>
#include <utility/test.hpp>
#include <utility/assumptions.hpp>
#include <utility/invariants.hpp>
#include <boost/chrono.hpp>
#include <vector>
#include <thread>


static void wait_milliseconds(natural_32_bit const num_millisecond)
{
    double const  max_duration = num_millisecond / 1000.0;
    for (boost::chrono::system_clock::time_point const  start = boost::chrono::system_clock::now();
         boost::chrono::duration<double>(boost::chrono::system_clock::now() - start).count() < max_duration;
         )
    {}
}

static void  thread_update_sensory_cells(
        efloop::access_to_sensory_cells&  access_to_sensory_cells,
        efloop::access_to_synapses_to_muscles const&  access_to_synapses_to_muscles,
        natural_32_bit  cell_index,
        natural_32_bit const  shift_to_next_cell
        )
{
    if (get_random_natural_32_bit_in_range(0U,10U) < 3U)
        wait_milliseconds(get_random_natural_32_bit_in_range(0U,1000U));

    std::shared_ptr<cellab::static_state_of_neural_tissue const> const  static_tissue =
            access_to_sensory_cells.get_static_state_of_tissue();

    for ( ; cell_index < static_tissue->num_sensory_cells(); cell_index += shift_to_next_cell)
    {
        instance_wrapper<my_cell> cell;
        access_to_sensory_cells.read_sensory_cell(cell_index,cell);
        cell->increment();
        access_to_sensory_cells.write_sensory_cell(cell_index,cell);

        for (natural_32_bit i = 0, n = get_random_natural_32_bit_in_range(0U,10U); i < n; ++i)
        {
            instance_wrapper<my_synapse> synapse;
            access_to_synapses_to_muscles.read_synapse_to_muscle(
                        get_random_natural_32_bit_in_range(0U,static_tissue->num_synapses_to_muscles()-1U),
                        synapse);
            TEST_SUCCESS(synapse->count() == cell->count());
        }
    }
}

void my_environment::compute_next_state(
        std::vector<efloop::access_to_sensory_cells>&  accesses_to_sensory_cells,
        std::vector<efloop::access_to_synapses_to_muscles>&  accesses_to_synapses_to_muscles,
        natural_32_bit const  num_threads_avalilable_for_computation
        )
{
    ASSUMPTION(accesses_to_sensory_cells.size() == accesses_to_synapses_to_muscles.size());
    ASSUMPTION(accesses_to_sensory_cells.size() > 0U);

    for (natural_32_bit i = 0U; i < accesses_to_sensory_cells.size(); ++i)
    {
        efloop::access_to_sensory_cells& access_to_sensory_cells = accesses_to_sensory_cells.at(i);
        efloop::access_to_synapses_to_muscles& access_to_synapses_to_muscles = accesses_to_synapses_to_muscles.at(i);

        std::vector<std::thread> threads;
        for (natural_32_bit i = 1U; i < num_threads_avalilable_for_computation; ++i)
            threads.push_back(
                        std::thread(
                            &thread_update_sensory_cells,
                            std::ref(access_to_sensory_cells),
                            std::ref(access_to_synapses_to_muscles),
                            i,
                            num_threads_avalilable_for_computation
                            )
                        );
        thread_update_sensory_cells(
                    access_to_sensory_cells,
                    access_to_synapses_to_muscles,
                    0U,
                    num_threads_avalilable_for_computation
                    );
        for(std::thread& thread : threads)
            thread.join();

        TEST_PROGRESS_UPDATE();
    }
}
