#include <netlab/network.hpp>
#include <utility/random.hpp>
#include <utility/assumptions.hpp>
#include <utility/invariants.hpp>
#include <utility/timeprof.hpp>
#include <utility/log.hpp>
#include <utility/development.hpp>
#include <array>
#include <algorithm>
#include <limits>
#include <iterator>

namespace netlab { namespace detail {


std::unique_ptr<extra_data_for_spikers_in_layers>  create_extra_data_for_spikers(network_props const&  props)
{
    TMPROF_BLOCK();

    auto data = std::unique_ptr<extra_data_for_spikers_in_layers>(new extra_data_for_spikers_in_layers);
    ASSUMPTION(data != nullptr);
    data->resize(props.layer_props().size(), extra_data_for_spikers_in_layers::value_type(0));
    for (layer_index_type i = 0U; i != props.layer_props().size(); ++i)
        data->at(i).resize(props.layer_props().at(i).num_spikers(), extra_data_for_spikers_in_one_layer::value_type(0));
    return std::move(data);
}


}}


std::string const&  to_string(netlab::NETWORK_STATE const  state)
{
    static std::array<std::string, 8ULL>  texts{
        "READY_FOR_CONSTRUCTION",                                       // 0U
        "READY_FOR_MOVEMENT_AREA_CENTERS_INITIALISATION",               // 1U
        "READY_FOR_MOVEMENT_AREA_CENTERS_MIGRATION_STARTUP",            // 2U
        "READY_FOR_MOVEMENT_AREA_CENTERS_MIGRATION_STEP",               // 3U
        "READY_FOR_COMPUTATION_OF_SHIP_DENSITIES_IN_LAYERS",            // 4U
        "READY_FOR_LUNCHING_SHIPS_INTO_MOVEMENT_AREAS",                 // 5U
        "READY_FOR_INITIALISATION_OF_MAP_FROM_DOCK_SECTORS_TO_SHIPS",   // 6U
        "READY_FOR_SIMULATION_STEP",                                    // 7U
    };
    ASSUMPTION(static_cast<natural_8_bit>(state) < texts.size());
    return texts.at(static_cast<natural_8_bit>(state));
}


namespace netlab {


network::network(std::shared_ptr<network_props> const  network_properties,
                 std::shared_ptr<network_layers_factory> const  layers_factory
                 )
    : m_properties(network_properties)
    , m_state(NETWORK_STATE::READY_FOR_CONSTRUCTION)
    , m_extra_data_for_spikers()
    , m_layers_of_spikers()
    , m_layers_of_docks()
    , m_layers_of_ships()
    , m_ships_in_sectors()
    , m_densities_of_ships()
    , m_update_id(0UL)
    , m_update_queue_of_ships()
    , m_max_size_of_update_queue_of_ships(0ULL)
    , m_is_update_queue_of_ships_overloaded(true)
    , m_use_update_queue_of_ships(true)
    , m_mini_spiking_random_generator()
    , m_current_spikers(std::make_unique< std::unordered_set<compressed_layer_and_object_indices> >())
    , m_next_spikers(std::make_unique< std::unordered_set<compressed_layer_and_object_indices> >())
{
    TMPROF_BLOCK();

    ASSUMPTION(this->properties() != nullptr);
    ASSUMPTION(layers_factory != nullptr);

    m_layers_of_spikers.reserve(properties()->layer_props().size());
    m_layers_of_docks.reserve(properties()->layer_props().size());
    m_layers_of_ships.reserve(properties()->layer_props().size());

    for (layer_index_type layer_index = 0U; layer_index < properties()->layer_props().size(); ++layer_index)
    {
        network_layer_props const&  layer_props = properties()->layer_props().at(layer_index);

        m_layers_of_spikers.emplace_back(layers_factory->create_layer_of_spikers(layer_index, layer_props.num_spikers()));
        ASSUMPTION(m_layers_of_spikers.back()->size() == layer_props.num_spikers());

        m_layers_of_docks.emplace_back(layers_factory->create_layer_of_docks(layer_index, layer_props.num_docks()));
        ASSUMPTION(m_layers_of_docks.back()->size() == layer_props.num_docks());

        m_layers_of_ships.emplace_back(layers_factory->create_layer_of_ships(layer_index, layer_props.num_ships()));
        ASSUMPTION(m_layers_of_ships.back()->size() == layer_props.num_ships());

        m_max_size_of_update_queue_of_ships += layer_props.num_ships();
    }

    m_max_size_of_update_queue_of_ships =
            std::max(1ULL,(natural_64_bit)std::round((float_64_bit)m_max_size_of_update_queue_of_ships * 1.0));

    m_state = NETWORK_STATE::READY_FOR_MOVEMENT_AREA_CENTERS_INITIALISATION;
}


void  network::initialise_movement_area_centers(initialiser_of_movement_area_centers&  area_centers_initialiser)
{
    TMPROF_BLOCK();

    ASSUMPTION(get_state() == NETWORK_STATE::READY_FOR_MOVEMENT_AREA_CENTERS_INITIALISATION);

    for (layer_index_type  layer_index = 0U; layer_index < properties()->layer_props().size(); ++layer_index)
    {
        network_layer_props const&  layer_props = properties()->layer_props().at(layer_index);

        area_centers_initialiser.on_next_layer(layer_index, *properties());

        layer_of_spikers&  spikers = *m_layers_of_spikers.at(layer_index);

        object_index_type  spiker_index = 0UL;
        for (sector_coordinate_type  c = 0U; c < layer_props.num_spikers_along_c_axis(); ++c)
            for (sector_coordinate_type  y = 0U; y < layer_props.num_spikers_along_y_axis(); ++y)
                for (sector_coordinate_type  x = 0U; x < layer_props.num_spikers_along_x_axis(); ++x)
                {
                    INVARIANT(spiker_index == layer_props.spiker_sector_index(x,y,c));

                    layer_index_type  area_layer_index;
                    area_centers_initialiser.compute_initial_movement_area_center_for_ships_of_spiker(
                            layer_index,
                            spiker_index,
                            x,y,c,
                            *properties(),
                            area_layer_index,
                            spikers.get_movement_area_center(spiker_index)
                            );
                        
                    ASSUMPTION(area_layer_index < properties()->layer_props().size());
                    ASSUMPTION(
                            [](vector3 const&  center, vector3 const&  size_of_ship_movement_area_in_meters,
                               vector3 const&  low_corner, vector3 const&  high_corner) -> bool {
                                vector3 const  area_shift = 0.5f * size_of_ship_movement_area_in_meters;
                                for (int i = 0; i != 3; ++i)
                                    if (center(i) - area_shift(i) < low_corner(i) - 0.001f ||
                                        center(i) + area_shift(i) > high_corner(i) + 0.001f )
                                        return false;
                                return true;
                                }(spikers.get_movement_area_center(spiker_index),
                                  layer_props.size_of_ship_movement_area_in_meters(area_layer_index),
                                  properties()->layer_props().at(area_layer_index).low_corner_of_ships(),
                                  properties()->layer_props().at(area_layer_index).high_corner_of_ships())
                            );
                    ASSUMPTION(
                            area_layer_index != layer_index ||
                            [](vector3 const&  spiker_pos, vector3 const&  spikers_dist,
                               vector3 const&  area_center, vector3 const&  area_size) -> bool {
                                vector3 const  area_shift = 0.5f * area_size;
                                vector3 const  delta = area_center - spiker_pos;
                                return std::abs(delta(0)) >= area_shift(0) + 0.5f * spikers_dist(0) ||
                                       std::abs(delta(1)) >= area_shift(1) + 0.5f * spikers_dist(1) ||
                                       std::abs(delta(2)) >= area_shift(2) + 0.5f * spikers_dist(2) ;
                                }(layer_props.spiker_sector_centre(x,y,c),layer_props.distance_of_spikers_in_meters(),
                                  spikers.get_movement_area_center(spiker_index),
                                  layer_props.size_of_ship_movement_area_in_meters(area_layer_index))
                            );

                    ++spiker_index;
                }
    }

    m_state = NETWORK_STATE::READY_FOR_MOVEMENT_AREA_CENTERS_MIGRATION_STARTUP;
}

void  network::prepare_for_movement_area_centers_migration(initialiser_of_movement_area_centers&  area_centers_initialiser)
{
    TMPROF_BLOCK();

    ASSUMPTION(get_state() == NETWORK_STATE::READY_FOR_MOVEMENT_AREA_CENTERS_MIGRATION_STARTUP);
    ASSUMPTION(m_extra_data_for_spikers == nullptr);

    m_extra_data_for_spikers = detail::create_extra_data_for_spikers(*properties());
    ASSUMPTION(m_extra_data_for_spikers != nullptr);
    access_to_movement_area_centers  movement_area_centers(&m_layers_of_spikers);
    accessor_to_extra_data_for_spikers_in_layers  extra_data_accessor(m_extra_data_for_spikers.get());
    area_centers_initialiser.prepare_for_shifting_movement_area_centers_in_layers(
            movement_area_centers,
            *properties(),
            extra_data_accessor
            );

    m_state = NETWORK_STATE::READY_FOR_MOVEMENT_AREA_CENTERS_MIGRATION_STEP;
}

void  network::do_movement_area_centers_migration_step(initialiser_of_movement_area_centers&  area_centers_initialiser)
{
    TMPROF_BLOCK();

    ASSUMPTION(get_state() == NETWORK_STATE::READY_FOR_MOVEMENT_AREA_CENTERS_MIGRATION_STEP);
    ASSUMPTION(m_extra_data_for_spikers != nullptr);

    accessor_to_extra_data_for_spikers_in_layers  extra_data_accessor(m_extra_data_for_spikers.get());

    std::vector<layer_index_type>  layers_to_update;
    area_centers_initialiser.get_indices_of_layers_where_to_apply_movement_area_centers_migration(
            *properties(),
            extra_data_accessor,
            layers_to_update
            );
    if (layers_to_update.empty())
    {
        if (false == area_centers_initialiser.do_extra_data_hold_densities_of_ships_per_spikers_in_layers())
            m_extra_data_for_spikers.reset();

        m_state = NETWORK_STATE::READY_FOR_COMPUTATION_OF_SHIP_DENSITIES_IN_LAYERS;
        return;
    }

    access_to_movement_area_centers  movement_area_centers(&m_layers_of_spikers);
    for (layer_index_type const  layer_index : layers_to_update)
    {
        network_layer_props const&  layer_props = properties()->layer_props().at(layer_index);

        layer_of_spikers&  spikers = *m_layers_of_spikers.at(layer_index);

        object_index_type  spiker_index = 0UL;
        for (sector_coordinate_type  c = 0U; c < layer_props.num_spikers_along_c_axis(); ++c)
            for (sector_coordinate_type  y = 0U; y < layer_props.num_spikers_along_y_axis(); ++y)
                for (sector_coordinate_type  x = 0U; x < layer_props.num_spikers_along_x_axis(); ++x)
                {
                    INVARIANT(spiker_index == layer_props.spiker_sector_index(x,y,c));

                    vector3&  center = spikers.get_movement_area_center(spiker_index);

                    layer_index_type const  area_layer_index = properties()->find_layer_index(center(2));

                    area_centers_initialiser.on_shift_movement_area_center_in_layer(
                            layer_index,
                            spiker_index,
                            x,y,c,
                            area_layer_index,
                            *properties(),
                            movement_area_centers,
                            center,
                            extra_data_accessor
                            );
                        
                    ASSUMPTION(
                            [](vector3 const&  center, vector3 const&  size_of_ship_movement_area_in_meters,
                                vector3 const&  low_corner, vector3 const&  high_corner) -> bool {
                                vector3 const  area_shift = 0.5f * size_of_ship_movement_area_in_meters;
                                for (int i = 0; i != 3; ++i)
                                    if (center(i) - area_shift(i) < low_corner(i) - 0.001f ||
                                        center(i) + area_shift(i) > high_corner(i) + 0.001f )
                                        return false;
                                return true;
                                }(center,layer_props.size_of_ship_movement_area_in_meters(area_layer_index),
                                  properties()->layer_props().at(area_layer_index).low_corner_of_ships(),
                                  properties()->layer_props().at(area_layer_index).high_corner_of_ships())
                            );
                    ASSUMPTION(
                            area_layer_index != layer_index ||
                            [](vector3 const&  spiker_pos, vector3 const&  spikers_dist,
                                vector3 const&  area_center, vector3 const&  area_size) -> bool {
                                vector3 const  area_shift = 0.5f * area_size;
                                vector3 const  delta = area_center - spiker_pos;
                                return std::abs(delta(0)) >= area_shift(0) + 0.5f * spikers_dist(0) ||
                                        std::abs(delta(1)) >= area_shift(1) + 0.5f * spikers_dist(1) ||
                                        std::abs(delta(2)) >= area_shift(2) + 0.5f * spikers_dist(2) ;
                                }(layer_props.spiker_sector_centre(x,y,c),layer_props.distance_of_spikers_in_meters(),
                                  center,layer_props.size_of_ship_movement_area_in_meters(area_layer_index))
                            );

                    ++spiker_index;
                }
    }
}


void  network::compute_densities_of_ships_in_layers()
{
    TMPROF_BLOCK();

    ASSUMPTION(get_state() == NETWORK_STATE::READY_FOR_COMPUTATION_OF_SHIP_DENSITIES_IN_LAYERS);

    if (m_extra_data_for_spikers == nullptr)
    {
        m_extra_data_for_spikers = detail::create_extra_data_for_spikers(*properties());
        accessor_to_extra_data_for_spikers_in_layers  extra_data_accessor(m_extra_data_for_spikers.get());
        
        initialise_densities_of_ships_per_spiker_in_layers(*properties(),extra_data_accessor);

        access_to_movement_area_centers  movement_area_centers(&m_layers_of_spikers);
        compute_densities_of_ships_per_spiker_in_layers(*properties(),movement_area_centers,extra_data_accessor);
    }
    {
        std::vector<float_32_bit>  ideal_densities;
        compute_ideal_densities_of_ships_in_layers(*properties(), ideal_densities);

        std::vector<float_32_bit>  minimal_densities;
        std::vector<float_32_bit>  maximal_densities;
        std::vector<float_32_bit>  average_densities;
        std::vector<distribution_of_spikers_by_density_of_ships>  distribution_of_spikers;
        compute_statistics_of_density_of_ships_in_layers(
                *properties(),
                accessor_to_extra_data_for_spikers_in_layers(m_extra_data_for_spikers.get()),
                ideal_densities,
                minimal_densities,
                maximal_densities,
                average_densities,
                distribution_of_spikers
                );
        m_densities_of_ships =
            std::unique_ptr<statistics_of_densities_of_ships_in_layers>(new statistics_of_densities_of_ships_in_layers(
                    ideal_densities,
                    minimal_densities,
                    maximal_densities,
                    average_densities,
                    distribution_of_spikers
                    ));
        ASSUMPTION(m_densities_of_ships != nullptr);
        ASSUMPTION(densities_of_ships().ideal_densities().size() == properties()->layer_props().size());
    }

    m_extra_data_for_spikers.reset();

    m_state = NETWORK_STATE::READY_FOR_LUNCHING_SHIPS_INTO_MOVEMENT_AREAS;
}


void  network::lunch_ships_into_movement_areas(initialiser_of_ships_in_movement_areas&  ships_initialiser)
{
    TMPROF_BLOCK();

    ASSUMPTION(get_state() == NETWORK_STATE::READY_FOR_LUNCHING_SHIPS_INTO_MOVEMENT_AREAS);

    for (layer_index_type  layer_index = 0U; layer_index < properties()->layer_props().size(); ++layer_index)
    {
        network_layer_props const&  layer_props = properties()->layer_props().at(layer_index);

        ships_initialiser.on_next_layer(layer_index, *properties());

        layer_of_ships&  ships = *m_layers_of_ships.at(layer_index);
        layer_of_spikers&  spikers = *m_layers_of_spikers.at(layer_index);

        object_index_type  spiker_index = 0UL;
        for (sector_coordinate_type  c = 0U; c < layer_props.num_spikers_along_c_axis(); ++c)
            for (sector_coordinate_type  y = 0U; y < layer_props.num_spikers_along_y_axis(); ++y)
                for (sector_coordinate_type  x = 0U; x < layer_props.num_spikers_along_x_axis(); ++x)
                {
                    INVARIANT(spiker_index == layer_props.spiker_sector_index(x,y,c));

                    ships_initialiser.on_next_area(layer_index, spiker_index, *properties());

                    vector3&  center = spikers.get_movement_area_center(spiker_index);

                    layer_index_type const  area_layer_index = properties()->find_layer_index(center(2));

                    object_index_type const  ships_begin_index = layer_props.ships_begin_index_of_spiker(spiker_index);
                    for (natural_32_bit  i = 0U; i < layer_props.num_ships_per_spiker(); ++i)
                    {
                        ships_initialiser.compute_ship_position_and_velocity_in_movement_area(
                                    center,
                                    i,
                                    layer_index,
                                    area_layer_index,
                                    *properties(),
                                    ships.get_position_nonconst_reference(ships_begin_index + i),
                                    ships.get_velocity_nonconst_reference(ships_begin_index + i)
                                    );
                        ASSUMPTION(
                                [](vector3 const&  center, network_layer_props const&  props,
                                   layer_index_type const  area_layer_index, vector3 const&  ship_position,
                                   vector3 const&  ship_velocity) -> bool {
                                    for (auto i = 0; i < 3; ++i)
                                        if (center(i) - 0.5f *
                                                props.size_of_ship_movement_area_in_meters(area_layer_index)(i)
                                                > ship_position(i) ||
                                            center(i) + 0.5f *
                                                props.size_of_ship_movement_area_in_meters(area_layer_index)(i)
                                                < ship_position(i))
                                            return false;

                                    float_32_bit  speed = length(ship_velocity);
                                    if (speed < props.min_speed_of_ship_in_meters_per_second(area_layer_index) ||
                                        speed > props.max_speed_of_ship_in_meters_per_second(area_layer_index) )
                                        return false;
                                    return true;
                                    }(center, layer_props, area_layer_index,
                                      ships.position(ships_begin_index + i),ships.velocity(ships_begin_index + i))
                                );
                    }

                    ++spiker_index;
                }
    }

    m_state = NETWORK_STATE::READY_FOR_INITIALISATION_OF_MAP_FROM_DOCK_SECTORS_TO_SHIPS;
}


void  network::initialise_map_from_dock_sectors_to_ships()
{
    TMPROF_BLOCK();

    ASSUMPTION(get_state() == NETWORK_STATE::READY_FOR_INITIALISATION_OF_MAP_FROM_DOCK_SECTORS_TO_SHIPS);

    m_ships_in_sectors.resize(properties()->layer_props().size());

    for (layer_index_type  layer_index = 0U; layer_index < properties()->layer_props().size(); ++layer_index)
    {
        network_layer_props const&  layer_props = properties()->layer_props().at(layer_index);

        std::vector<compressed_layer_and_object_indices>  empty_dock_sector;
        empty_dock_sector.reserve(3UL + layer_props.num_ships() / layer_props.num_docks());
        m_ships_in_sectors.at(layer_index).resize(layer_props.num_docks(), empty_dock_sector);
    }

    for (layer_index_type  layer_index = 0U; layer_index < properties()->layer_props().size(); ++layer_index)
        for (object_index_type  ship_index = 0UL; ship_index < m_layers_of_ships.at(layer_index)->size(); ++ship_index)
        {
            network_layer_props const&  ship_layer_props = properties()->layer_props().at(layer_index);
            object_index_type const  spiker_sector_index = ship_layer_props.spiker_index_from_ship_index(ship_index);
            vector3 const&  movement_area_center = m_layers_of_spikers.at(layer_index)->get_movement_area_center(spiker_sector_index);
            layer_index_type const  area_layer_index = properties()->find_layer_index(movement_area_center(2));
            ASSUMPTION(area_layer_index < properties()->layer_props().size());
            network_layer_props const&  area_layer_props = properties()->layer_props().at(area_layer_index);
            object_index_type  sector_index;
            {
                sector_coordinate_type  x, y, c;
                area_layer_props.dock_sector_coordinates(m_layers_of_ships.at(layer_index)->position(ship_index), x, y, c);
                sector_index = area_layer_props.dock_sector_index(x, y, c);
            }
            ASSUMPTION(sector_index < m_ships_in_sectors.at(area_layer_index).size());
            m_ships_in_sectors.at(area_layer_index).at(sector_index).push_back({ layer_index, ship_index });
        }

    m_state = NETWORK_STATE::READY_FOR_SIMULATION_STEP;
}


extra_data_for_spikers_in_one_layer::value_type  network::get_extra_data_of_spiker(
        layer_index_type const  layer_index,
        object_index_type const  object_index
        ) const
{
    ASSUMPTION(get_state() == NETWORK_STATE::READY_FOR_MOVEMENT_AREA_CENTERS_MIGRATION_STEP);
    ASSUMPTION(m_extra_data_for_spikers != nullptr);
    accessor_to_extra_data_for_spikers_in_layers const  extra_data_accessor(m_extra_data_for_spikers.get());
    return extra_data_accessor.get_extra_data_of_spiker(layer_index,object_index);
}


void  network::do_simulation_step(
        const bool  use_spiking,
        const bool  use_mini_spiking,
        const bool  use_movement_of_ships,
        tracked_network_object_stats* const  stats_of_tracked_object
        )
{
    TMPROF_BLOCK();

    ASSUMPTION(get_state() == NETWORK_STATE::READY_FOR_SIMULATION_STEP);

    ++m_update_id;

    if (use_movement_of_ships)
        update_movement_of_ships(dynamic_cast<tracked_ship_stats*>(stats_of_tracked_object));

    if (use_mini_spiking)
        update_mini_spiking(use_spiking,stats_of_tracked_object);

    if (use_spiking)
        update_spiking(stats_of_tracked_object);
}


void  network::update_movement_of_ships(tracked_ship_stats* const  stats_of_tracked_ship)
{
    TMPROF_BLOCK();

    if (is_update_queue_of_ships_overloaded() || !is_update_queue_of_ships_used())
    {
        m_is_update_queue_of_ships_overloaded = !is_update_queue_of_ships_used();
        m_update_queue_of_ships.clear();

        for (layer_index_type  layer_index = 0U; layer_index < properties()->layer_props().size(); ++layer_index)
        {
            if (properties()->layer_props().at(layer_index).ship_controller_ptr() == nullptr)
                continue;

            network_layer_props const&  ship_layer_props = properties()->layer_props().at(layer_index);

            for (object_index_type  ship_index_in_layer = 0ULL, num_ships = m_layers_of_ships.at(layer_index)->size();
                    ship_index_in_layer < num_ships;
                    ++ship_index_in_layer
                    )
            {
                update_movement_of_ship(layer_index,ship_index_in_layer,stats_of_tracked_ship);

                layer_index_type const  area_layer_index =
                        properties()->find_layer_index(
                            m_layers_of_spikers.at(layer_index)->get_movement_area_center(
                                ship_layer_props.spiker_index_from_ship_index(ship_index_in_layer)
                                )(2)
                            );
                network_layer_props const&  area_layer_props = properties()->layer_props().at(area_layer_index);

                layer_of_ships const&  ships = *m_layers_of_ships.at(layer_index);
                if (!is_update_queue_of_ships_overloaded() && is_update_queue_of_ships_used() &&
                    !area_layer_props.ship_controller_ptr()->is_ship_docked(
                            ships.position(ship_index_in_layer),
                            ships.velocity(ship_index_in_layer),
                            area_layer_index,
                            *properties()
                            ))
                {
                    m_update_queue_of_ships.push_back({layer_index,ship_index_in_layer});
                    if (m_update_queue_of_ships.size() > max_size_of_update_queue_of_ships())
                        m_is_update_queue_of_ships_overloaded = true;
                }
            }
        }
    }
    else
    {
        for (natural_64_bit  i = 0ULL, n = m_update_queue_of_ships.size(); i != n; ++i)
        {
            INVARIANT(!m_update_queue_of_ships.empty());

            auto const  ship_id = m_update_queue_of_ships.front();
            m_update_queue_of_ships.pop_front();

            update_movement_of_ship(ship_id.layer_index(),ship_id.object_index(),stats_of_tracked_ship);

            network_layer_props const&  ship_layer_props = properties()->layer_props().at(ship_id.layer_index());
            layer_index_type const  area_layer_index =
                    properties()->find_layer_index(
                        m_layers_of_spikers.at(ship_id.layer_index())->get_movement_area_center(
                            ship_layer_props.spiker_index_from_ship_index(ship_id.object_index())
                            )(2)
                        );
            network_layer_props const&  area_layer_props = properties()->layer_props().at(area_layer_index);

            layer_of_ships const&  ships = *m_layers_of_ships.at(ship_id.layer_index());
            if (!area_layer_props.ship_controller_ptr()->is_ship_docked(
                        ships.position(ship_id.object_index()),
                        ships.velocity(ship_id.object_index()),
                        area_layer_index,
                        *properties()
                        ))
                m_update_queue_of_ships.push_back(ship_id);
        }
    }
}


void  network::update_movement_of_ship(
        layer_index_type const  layer_index,
        object_index_type const  ship_index_in_layer,
        tracked_ship_stats*  stats_of_tracked_ship
        )
{
    TMPROF_BLOCK();

    vector3&  ship_position_ref = m_layers_of_ships.at(layer_index)->get_position_nonconst_reference(ship_index_in_layer);
    vector3&  ship_velocity_ref = m_layers_of_ships.at(layer_index)->get_velocity_nonconst_reference(ship_index_in_layer);

    compressed_layer_and_object_indices const  ship_loc(layer_index,ship_index_in_layer);

    if (stats_of_tracked_ship != nullptr && ship_loc != stats_of_tracked_ship->indices())
        stats_of_tracked_ship = nullptr;

    network_layer_props const&  ship_layer_props = properties()->layer_props().at(layer_index);

    object_index_type const  spiker_sector_index = ship_layer_props.spiker_index_from_ship_index(ship_index_in_layer);

    vector3 const&  movement_area_center = m_layers_of_spikers.at(layer_index)->get_movement_area_center(spiker_sector_index);

    layer_index_type const  area_layer_index = properties()->find_layer_index(movement_area_center(2));

    vector3 const  movement_area_low_corner =
            movement_area_center - 0.5f * ship_layer_props.size_of_ship_movement_area_in_meters(area_layer_index);
    vector3 const  movement_area_high_corner =
            movement_area_center + 0.5f * ship_layer_props.size_of_ship_movement_area_in_meters(area_layer_index);

    std::vector< std::vector<compressed_layer_and_object_indices> >&  ships_in_sectors =
            m_ships_in_sectors.at(area_layer_index);

    network_layer_props const&  area_layer_props = properties()->layer_props().at(area_layer_index);

    vector3  dock_sector_center_of_ship;
    bool  dock_sector_belongs_to_the_same_spiker_as_the_ship;
    {
        sector_coordinate_type  x, y, c;
        area_layer_props.dock_sector_coordinates(ship_position_ref, x,y,c);
        dock_sector_center_of_ship = area_layer_props.dock_sector_centre(x,y,c);

        if (layer_index == area_layer_index)
        {
            object_index_type  spiker_index;
            {
                sector_coordinate_type  spiker_x, spiker_y, spiker_c;
                area_layer_props.spiker_sector_coordinates_from_dock_sector_coordinates(
                        x, y, c,
                        spiker_x, spiker_y, spiker_c
                        );
                spiker_index = area_layer_props.spiker_sector_index(spiker_x, spiker_y, spiker_c);
            }
            dock_sector_belongs_to_the_same_spiker_as_the_ship = (spiker_index == spiker_sector_index);
        }
        else
            dock_sector_belongs_to_the_same_spiker_as_the_ship = false;
    }

    vector3  ship_acceleration =
        area_layer_props.ship_controller_ptr()->accelerate_ship_in_environment(
                ship_velocity_ref,
                layer_index,
                area_layer_index,
                *properties());
    {
        ship_acceleration += area_layer_props.ship_controller_ptr()->accelerate_into_space_box(
                ship_position_ref,
                ship_velocity_ref,
                movement_area_center,
                layer_index,
                area_layer_index,
                *properties()
                );

        sector_coordinate_type  x_lo, y_lo, c_lo;
        sector_coordinate_type  x_hi, y_hi, c_hi;
        {
            vector3 const  range_vector(
                    area_layer_props.ship_controller_ptr()->docks_enumerations_distance_for_accelerate_into_dock(),
                    area_layer_props.ship_controller_ptr()->docks_enumerations_distance_for_accelerate_into_dock(),
                    area_layer_props.ship_controller_ptr()->docks_enumerations_distance_for_accelerate_into_dock()
                    );
            area_layer_props.dock_sector_coordinates(ship_position_ref - range_vector, x_lo, y_lo, c_lo);
            area_layer_props.dock_sector_coordinates(ship_position_ref + range_vector, x_hi, y_hi, c_hi);
        }
        for (sector_coordinate_type x = x_lo; x <= x_hi; ++x)
            for (sector_coordinate_type y = y_lo; y <= y_hi; ++y)
                for (sector_coordinate_type c = c_lo; c <= c_hi; ++c)
                {
                    vector3 const  sector_centre = area_layer_props.dock_sector_centre(x,y,c);

                    if (sector_centre(0) < movement_area_low_corner(0) || sector_centre(0) > movement_area_high_corner(0) || 
                        sector_centre(1) < movement_area_low_corner(1) || sector_centre(1) > movement_area_high_corner(1) || 
                        sector_centre(2) < movement_area_low_corner(2) || sector_centre(2) > movement_area_high_corner(2) )
                        continue;

                    bool  dock_belongs_to_the_same_spiker_as_the_ship;
                    {
                        if (layer_index == area_layer_index)
                        {
                            object_index_type  spiker_index;
                            {
                                sector_coordinate_type  spiker_x, spiker_y, spiker_c;
                                area_layer_props.spiker_sector_coordinates_from_dock_sector_coordinates(
                                            x,y,c,
                                            spiker_x,spiker_y,spiker_c
                                            );
                                spiker_index = area_layer_props.spiker_sector_index(spiker_x,spiker_y,spiker_c);
                            }
                            dock_belongs_to_the_same_spiker_as_the_ship = (spiker_index == spiker_sector_index);
                        }
                        else
                            dock_belongs_to_the_same_spiker_as_the_ship = false;
                    }

                    if (dock_belongs_to_the_same_spiker_as_the_ship)
                        ship_acceleration += area_layer_props.ship_controller_ptr()->accelerate_from_dock(
                                ship_position_ref,
                                ship_velocity_ref,
                                sector_centre,
                                layer_index,
                                area_layer_index,
                                *properties()
                                );
                    else
                        ship_acceleration += area_layer_props.ship_controller_ptr()->accelerate_into_dock(
                                ship_position_ref,
                                ship_velocity_ref,
                                sector_centre,
                                layer_index,
                                area_layer_index,
                                *properties()
                                );
                }

        if (ship_position_ref(0) >= movement_area_low_corner(0) && ship_position_ref(0) <= movement_area_high_corner(0) &&
            ship_position_ref(1) >= movement_area_low_corner(1) && ship_position_ref(1) <= movement_area_high_corner(1) &&
            ship_position_ref(2) >= movement_area_low_corner(2) && ship_position_ref(2) <= movement_area_high_corner(2))
        {
            vector3 const  range_vector(
                area_layer_props.ship_controller_ptr()->docks_enumerations_distance_for_accelerate_from_ship(),
                area_layer_props.ship_controller_ptr()->docks_enumerations_distance_for_accelerate_from_ship(),
                area_layer_props.ship_controller_ptr()->docks_enumerations_distance_for_accelerate_from_ship()
                );
            area_layer_props.dock_sector_coordinates(ship_position_ref- range_vector, x_lo, y_lo, c_lo);
            area_layer_props.dock_sector_coordinates(ship_position_ref + range_vector, x_hi, y_hi, c_hi);
            for (sector_coordinate_type x = x_lo; x <= x_hi; ++x)
                for (sector_coordinate_type y = y_lo; y <= y_hi; ++y)
                    for (sector_coordinate_type c = c_lo; c <= c_hi; ++c)
                    {
                        object_index_type const  sector_index = area_layer_props.dock_sector_index(x,y,c);
                        for (compressed_layer_and_object_indices const  loc : ships_in_sectors.at(sector_index))
                            if (loc != ship_loc)
                                ship_acceleration += area_layer_props.ship_controller_ptr()->accelerate_from_ship(
                                        ship_position_ref,
                                        ship_velocity_ref,
                                        m_layers_of_ships.at(loc.layer_index())->position(loc.object_index()),
                                        m_layers_of_ships.at(loc.layer_index())->velocity(loc.object_index()),
                                        dock_sector_center_of_ship,
                                        dock_sector_belongs_to_the_same_spiker_as_the_ship,
                                        layer_index,
                                        area_layer_index,
                                        *properties()
                                        );
                    }
        }
    }

    float_32_bit const  dt = properties()->update_time_step_in_seconds();

    vector3  new_velocity = ship_velocity_ref + dt * ship_acceleration;
    {
        float_32_bit const  new_speed = length(new_velocity);
        if (new_speed < ship_layer_props.min_speed_of_ship_in_meters_per_second(area_layer_index))
            area_layer_props.ship_controller_ptr()->on_too_slow(
                    new_velocity,
                    ship_position_ref,
                    new_speed,
                    dock_sector_center_of_ship,
                    layer_index,
                    area_layer_index,
                    *properties()
                    );
        else if (new_speed > ship_layer_props.max_speed_of_ship_in_meters_per_second(area_layer_index))
            area_layer_props.ship_controller_ptr()->on_too_fast(
                    new_velocity,
                    ship_position_ref,
                    new_speed,
                    dock_sector_center_of_ship,
                    layer_index,
                    area_layer_index,
                    *properties()
                    );
    }

    vector3 const  new_position = ship_position_ref + dt * new_velocity;

    object_index_type  old_sector_index;
    {
        sector_coordinate_type  x, y, c;
        area_layer_props.dock_sector_coordinates(ship_position_ref, x, y, c);
        old_sector_index = area_layer_props.dock_sector_index(x,y,c);
    }
    object_index_type  new_sector_index;
    {
        sector_coordinate_type  x, y, c;
        area_layer_props.dock_sector_coordinates(new_position, x, y, c);
        new_sector_index = area_layer_props.dock_sector_index(x,y,c);
    }
    if (new_sector_index != old_sector_index)
    {
        std::vector<compressed_layer_and_object_indices>&  old_sector = ships_in_sectors.at(old_sector_index);
        auto  it = old_sector.begin();
        while (true)
        {
            INVARIANT(it != old_sector.end());
            if (*it == ship_loc)
                break;
            ++it;
        }
        *it = old_sector.back();
        old_sector.pop_back();

        ships_in_sectors.at(new_sector_index).push_back(ship_loc);
    }

    ship_position_ref = new_position;
    ship_velocity_ref = new_velocity;
}


void  network::update_mini_spiking(
        const bool  use_spiking,
        tracked_network_object_stats* const  stats_of_tracked_object
        )
{
    TMPROF_BLOCK();

    std::vector<natural_64_bit>  counts_of_ships{0ULL};
    for (layer_index_type  layer_index = 0U; layer_index != properties()->layer_props().size(); ++layer_index)
        counts_of_ships.push_back(counts_of_ships.back() + properties()->layer_props().at(layer_index).num_ships());

    for (natural_64_bit i = 0ULL, n = properties()->num_mini_spikes_to_generate_per_simulation_step(); i != n; ++i)
    {
        natural_64_bit const  ship_super_index =
                get_random_natural_64_bit_in_range(0ULL,properties()->num_ships() - 1ULL,m_mini_spiking_random_generator);

        auto const  layer_it = std::upper_bound(counts_of_ships.cbegin(),counts_of_ships.cend(),ship_super_index);
        INVARIANT(layer_it != counts_of_ships.cbegin() && layer_it != counts_of_ships.cend());
        layer_index_type const  layer_index =
            (layer_index_type)std::distance(counts_of_ships.cbegin(),layer_it) - 1U;
        INVARIANT(layer_index < properties()->layer_props().size());
        object_index_type const  ship_index = ship_super_index - counts_of_ships.at(layer_index);
        network_layer_props const&  ship_layer_props = properties()->layer_props().at(layer_index);
        INVARIANT(ship_index < ship_layer_props.num_ships());

        layer_index_type const  area_layer_index = properties()->find_layer_index(
            m_layers_of_spikers.at(layer_index)->get_movement_area_center(ship_layer_props.spiker_index_from_ship_index(ship_index))(2)
            );
        network_layer_props const&  area_layer_props = properties()->layer_props().at(area_layer_index);
        sector_coordinate_type  dock_x,dock_y,dock_c;
        area_layer_props.dock_sector_coordinates(m_layers_of_ships.at(layer_index)->position(ship_index),dock_x,dock_y,dock_c);
        vector3 const  nearest_dock_pos = area_layer_props.dock_sector_centre(dock_x,dock_y,dock_c);

        if (are_ship_and_dock_connected(
                    m_layers_of_ships.at(layer_index)->position(ship_index),
                    nearest_dock_pos,
                    properties()->max_connection_distance_in_meters()))
        {
            sector_coordinate_type  spiker_x,spiker_y,spiker_c;
            area_layer_props.spiker_sector_coordinates_from_dock_sector_coordinates(dock_x,dock_y,dock_c,spiker_x,spiker_y,spiker_c);

            object_index_type const  spiker_index = area_layer_props.spiker_sector_index(spiker_x,spiker_y,spiker_c);
            vector3 const  spiker_pos = area_layer_props.spiker_sector_centre(spiker_x,spiker_y,spiker_c);

            object_index_type const  dock_index = area_layer_props.dock_sector_index(dock_x,dock_y,dock_c);
            float_32_bit const  mini_potential_on_spiker =
                    m_layers_of_docks.at(area_layer_index)->on_arrival_of_mini_spiking_potential(
                            dock_index,
                            properties()->layer_props().at(layer_index).are_spikers_excitatory(),
                            spiker_pos,
                            nearest_dock_pos,
                            *properties()
                            );

            m_layers_of_spikers.at(area_layer_index)->update_spiking_potential(spiker_index,m_update_id,*properties());

            bool const  did_mini_spike_cause_spike_generation =
                    m_layers_of_spikers.at(area_layer_index)->on_arrival_of_postsynaptic_potential(
                            spiker_index,
                            mini_potential_on_spiker,
                            *properties());

            if (use_spiking)
                if (did_mini_spike_cause_spike_generation)
                    m_next_spikers->insert({area_layer_index,spiker_index});
                else
                    m_next_spikers->erase({area_layer_index,spiker_index});
        }
    }
}


void  network::update_spiking(
        tracked_network_object_stats* const  stats_of_tracked_object
        )
{
    TMPROF_BLOCK();

    for (auto const spiker_id : *m_current_spikers)
    {
        layer_index_type const  spiker_layer_index = spiker_id.layer_index();
        object_index_type const  spiker_index = spiker_id.object_index();

        network_layer_props const&  spiker_layer_props = properties()->layer_props().at(spiker_layer_index);

        sector_coordinate_type  spiker_x,spiker_y,spiker_c;
        spiker_layer_props.spiker_sector_coordinates(spiker_index, spiker_x,spiker_y,spiker_c);
        vector3 const  spiker_position = spiker_layer_props.spiker_sector_centre(spiker_x,spiker_y,spiker_c);

        layer_index_type const  area_layer_index = properties()->find_layer_index(
                m_layers_of_spikers.at(spiker_layer_index)->get_movement_area_center(spiker_index)(2)
                );
        network_layer_props const&  area_layer_props = properties()->layer_props().at(area_layer_index);

        object_index_type const  ships_begin_index = spiker_layer_props.ships_begin_index_of_spiker(spiker_index);
        for (natural_32_bit  i = 0U; i != spiker_layer_props.num_ships_per_spiker(); ++i)
        {
            layer_of_ships&  ships = *m_layers_of_ships.at(spiker_layer_index);

            sector_coordinate_type  dock_x,dock_y,dock_c;
            area_layer_props.dock_sector_coordinates(ships.position(ships_begin_index + i),dock_x,dock_y,dock_c);
            vector3 const  dock_position = area_layer_props.dock_sector_centre(dock_x,dock_y,dock_c);

            if (are_ship_and_dock_connected(
                        ships.position(ships_begin_index + i),
                        dock_position,
                        properties()->max_connection_distance_in_meters()))
            {
                sector_coordinate_type  target_spiker_x,target_spiker_y,target_spiker_c;
                area_layer_props.spiker_sector_coordinates_from_dock_sector_coordinates(
                        dock_x,dock_y,dock_c,
                        target_spiker_x,target_spiker_y,target_spiker_c
                        );
                vector3 const  target_spiker_position = area_layer_props.spiker_sector_centre(
                        target_spiker_x,target_spiker_y,target_spiker_c
                        );
                object_index_type const  target_spiker_index =
                        area_layer_props.spiker_sector_index(target_spiker_x,target_spiker_y,target_spiker_c);

                layer_of_spikers&  target_spikers = *m_layers_of_spikers.at(area_layer_index);
                layer_of_docks&  docks = *m_layers_of_docks.at(area_layer_index);

                object_index_type const  dock_index = area_layer_props.dock_sector_index(dock_x,dock_y,dock_c);

                float_32_bit const  potential_of_the_target_spiker_at_dock =
                        docks.compute_potential_of_spiker_at_dock(
                                dock_index,
                                target_spikers.get_potential(target_spiker_index),
                                target_spiker_position,
                                dock_position,
                                *properties()
                                );

                float_32_bit const  potential_delta_at_dock =
                        ships.on_arrival_of_presynaptic_potential(
                                ships_begin_index + i,
                                potential_of_the_target_spiker_at_dock,
                                area_layer_index,
                                *properties()
                                );

                float_32_bit const  potential_delta_at_target_spiker =
                        docks.on_arrival_of_postsynaptic_potential(
                                dock_index,
                                potential_delta_at_dock,
                                target_spiker_position,
                                dock_position,
                                spiker_layer_index,
                                *properties()
                                );

                bool const  does_posynaptic_potential_causes_generation_of_spike =
                        target_spikers.on_arrival_of_postsynaptic_potential(
                                target_spiker_index,
                                potential_delta_at_target_spiker,
                                *properties()
                                );

                if (does_posynaptic_potential_causes_generation_of_spike)
                    m_next_spikers->insert({area_layer_index,target_spiker_index});
                else
                    m_next_spikers->erase({area_layer_index,target_spiker_index});
            }
        }

        object_index_type const  docks_begin_index = spiker_layer_props.docks_begin_index_of_spiker(spiker_index);
        for (natural_32_bit  i = 0U; i != spiker_layer_props.num_docks_per_spiker(); ++i)
        {
            sector_coordinate_type  dock_x,dock_y,dock_c;
            spiker_layer_props.dock_sector_coordinates(docks_begin_index + i,dock_x,dock_y,dock_c);
            vector3 const  dock_position = spiker_layer_props.dock_sector_centre(dock_x,dock_y,dock_c);

            for (compressed_layer_and_object_indices const  ship_idx : m_ships_in_sectors.at(spiker_layer_index).at(docks_begin_index + i))
            {
                layer_of_ships&  ships = *m_layers_of_ships.at(ship_idx.layer_index());
                if (are_ship_and_dock_connected(
                            ships.position(ship_idx.object_index()),
                            dock_position,
                            properties()->max_connection_distance_in_meters()))
                {
                    float_32_bit const  potential_of_the_target_spiker_at_dock =
                            m_layers_of_docks.at(spiker_layer_index)->compute_potential_of_spiker_at_dock(
                                    docks_begin_index + i,
                                    m_layers_of_spikers.at(spiker_layer_index)->get_potential(spiker_index),
                                    spiker_position,
                                    dock_position,
                                    *properties()
                                    );

                    float_32_bit const  potential_delta_for_connected_ship =
                            m_layers_of_docks.at(spiker_layer_index)->on_arrival_of_presynaptic_potential(
                                    docks_begin_index + i,
                                    m_layers_of_spikers.at(spiker_layer_index)->get_potential(spiker_index),
                                    ship_idx.layer_index(),
                                    *properties()
                                    );

                    ships.on_arrival_of_postsynaptic_potential(
                            ship_idx.object_index(),
                            potential_delta_for_connected_ship,
                            ship_idx.layer_index(),
                            *properties()
                            );

                    break;
                }
            }
        }
    }

    std::swap(m_current_spikers, m_next_spikers);
    m_next_spikers->clear();
}


}
