#ifndef QTGL_DETAIL_MODELSPACE_HPP_INCLUDED
#   define QTGL_DETAIL_MODELSPACE_HPP_INCLUDED

#   include <utility/async_resource_load.hpp>
#   include <angeo/coordinate_system.hpp>
#   include <boost/filesystem/path.hpp>
#   include <vector>
#   include <memory>

namespace qtgl { namespace detail {


struct  modelspace_data
{
    modelspace_data(async::key_type const&  key, async::finalise_load_on_destroy_ptr);
    ~modelspace_data();

    std::vector<angeo::coordinate_system> const&  coord_systems() const { return m_coord_systems; }

private:

    std::vector<angeo::coordinate_system>  m_coord_systems;
};


}}

namespace qtgl {


struct  modelspace : public async::resource_accessor<detail::modelspace_data>
{
    modelspace()
        : async::resource_accessor<detail::modelspace_data>()
    {}

    explicit modelspace(boost::filesystem::path const&  path)
        : async::resource_accessor<detail::modelspace_data>(
            {"qtgl::modelspace",path.string()},
            1U
            )
    {}

    std::vector<angeo::coordinate_system> const&  get_coord_systems() const
    { return resource().coord_systems(); }

    boost::filesystem::path  get_skeleton_path() const { return boost::filesystem::path(key().second).parent_path(); }
};


}

#endif
