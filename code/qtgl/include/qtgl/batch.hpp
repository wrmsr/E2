#ifndef QTGL_BATCH_HPP_INCLUDED
#   define QTGL_BATCH_HPP_INCLUDED

#   include <qtgl/buffer.hpp>
#   include <qtgl/shader.hpp>
#   include <qtgl/texture.hpp>
#   include <boost/filesystem/path.hpp>
#   include <unordered_set>
#   include <memory>

namespace qtgl {


struct batch
{
    batch(boost::filesystem::path const&  path,
          buffers_binding_ptr const  buffers_binding,
          shaders_binding_ptr const  shaders_binding,
          textures_binding_ptr const  textures_binding
          );

    boost::filesystem::path const&  path() const noexcept { return m_path; }

    buffers_binding_ptr  buffers_binding() const noexcept { return m_buffers_binding; }
    shaders_binding_ptr  shaders_binding() const noexcept { return m_shaders_binding; }
    textures_binding_ptr  textures_binding() const noexcept { return m_textures_binding; }

    std::unordered_set<vertex_shader_uniform_symbolic_name> const&  symbolic_names_of_used_uniforms() const;

private:

    boost::filesystem::path  m_path;
    buffers_binding_ptr  m_buffers_binding;
    shaders_binding_ptr  m_shaders_binding;
    textures_binding_ptr  m_textures_binding;

    static std::unordered_set<vertex_shader_uniform_symbolic_name>  s_empty_uniforms;
};


std::shared_ptr<batch const>  load_batch_file(boost::filesystem::path const&  batch_file, std::string&  error_message);


bool  make_current(batch const&  binding);


}

#endif
