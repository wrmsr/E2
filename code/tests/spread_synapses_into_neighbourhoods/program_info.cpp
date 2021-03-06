#include "./program_info.hpp"

std::string  get_program_name()
{
    return "spread_synapses_into_neighbourhoods";
}

std::string  get_program_version()
{
    return "0.01";
}

std::string  get_program_description()
{
    return  "This program tests cellconnect's algorithm for spreading synapses\n"
            "from territories of cells in single columns to territories of\n"
            "cells in their neighbourhoods. The test builds four tissues of\n"
            "different xy-sizes, for four different kinds of tissue cells,\n"
            "and four different kinds of sensory cells. For each such\n"
            "tissue synapses in columns are filled in using the algorithm\n"
            "'fill_src_coords_of_synapses'. Then the algorithm for spreading\n"
            "synapses is called for each pair of kinds of tissue cells, for two\n"
            "pairs of xy-diameters of neighbourhoods, and for 1 and 16 available\n"
            "threads. Each odd/even call to the algorithm is passed identity/general\n"
            "column shift function. Once all synapses are spread, then for each column\n"
            "and for each pair of kinds of cells there is checked whether counts of\n"
            "synapses in all columns in the neighbourhood of the checked column equals\n"
            "to counts inside the distribution matrix build and passed to the algorithm."
            ;
}
