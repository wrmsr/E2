#include <qtgl/shader_data_bindings.hpp>
#include <utility/invariants.hpp>
#include <utility/assumptions.hpp>
#include <unordered_map>

namespace qtgl {


std::string  name(VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION const  location)
{
    switch (location)
    {
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_POSITION : return "BINDING_IN_POSITION";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_DIFFUSE  : return "BINDING_IN_DIFFUSE";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_SPECULAR : return "BINDING_IN_SPECULAR";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_NORMAL   : return "BINDING_IN_NORMAL";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_INDICES_OF_MATRICES: return "BINDING_IN_INDICES_OF_MATRICES";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_WEIGHTS_OF_MATRICES: return "BINDING_IN_WEIGHTS_OF_MATRICES";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD0: return "BINDING_IN_TEXCOORD0";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD1: return "BINDING_IN_TEXCOORD1";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD2: return "BINDING_IN_TEXCOORD2";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD3: return "BINDING_IN_TEXCOORD3";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD4: return "BINDING_IN_TEXCOORD4";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD5: return "BINDING_IN_TEXCOORD5";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD6: return "BINDING_IN_TEXCOORD6";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD7: return "BINDING_IN_TEXCOORD7";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD8: return "BINDING_IN_TEXCOORD8";
    case VERTEX_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD9: return "BINDING_IN_TEXCOORD9";
    default: UNREACHABLE();
    }
}

std::string  name(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION const  location)
{
    switch (location)
    {
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_POSITION : return "BINDING_OUT_POSITION";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_DIFFUSE  : return "BINDING_OUT_DIFFUSE";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_SPECULAR : return "BINDING_OUT_SPECULAR";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_NORMAL   : return "BINDING_OUT_NORMAL";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD0: return "BINDING_OUT_TEXCOORD0";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD1: return "BINDING_OUT_TEXCOORD1";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD2: return "BINDING_OUT_TEXCOORD2";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD3: return "BINDING_OUT_TEXCOORD3";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD4: return "BINDING_OUT_TEXCOORD4";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD5: return "BINDING_OUT_TEXCOORD5";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD6: return "BINDING_OUT_TEXCOORD6";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD7: return "BINDING_OUT_TEXCOORD7";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD8: return "BINDING_OUT_TEXCOORD8";
    case VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD9: return "BINDING_OUT_TEXCOORD9";
    default: UNREACHABLE();
    }
}

std::string  name(VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME const  symbolic_name)
{
    switch (symbolic_name)
    {
    case VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME::DIFFUSE_COLOUR: return "DIFFUSE_COLOUR";
    case VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME::TRANSFORM_MATRIX_TRANSPOSED: return "TRANSFORM_MATRIX_TRANSPOSED";
    case VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME::TRANSFORM_MATRICES_TRANSPOSED: return "TRANSFORM_MATRICES_TRANSPOSED";
    case VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME::NUM_MATRICES_PER_VERTEX: return "NUM_MATRICES_PER_VERTEX";
    default: UNREACHABLE();
    }
}

VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME  to_symbolic_uniform_name_of_vertex_shader(std::string  name)
{
    if (name.find("UNIFORM_") == 0UL)
        name = name.substr(std::strlen("UNIFORM_"));

    if (name == "DIFFUSE_COLOUR")
        return VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME::DIFFUSE_COLOUR;
    if (name == "TRANSFORM_MATRIX_TRANSPOSED")
        return VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME::TRANSFORM_MATRIX_TRANSPOSED;
    if (name == "TRANSFORM_MATRICES_TRANSPOSED")
        return VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME::TRANSFORM_MATRICES_TRANSPOSED;
    if (name == "NUM_MATRICES_PER_VERTEX")
        return VERTEX_SHADER_UNIFORM_SYMBOLIC_NAME::NUM_MATRICES_PER_VERTEX;

    UNREACHABLE();
}

std::string  name(FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION const  location)
{
    switch (location)
    {
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_POSITION : return "BINDING_IN_POSITION";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_DIFFUSE  : return "BINDING_IN_DIFFUSE";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_SPECULAR : return "BINDING_IN_SPECULAR";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_NORMAL   : return "BINDING_IN_NORMAL";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD0: return "BINDING_IN_TEXCOORD0";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD1: return "BINDING_IN_TEXCOORD1";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD2: return "BINDING_IN_TEXCOORD2";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD3: return "BINDING_IN_TEXCOORD3";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD4: return "BINDING_IN_TEXCOORD4";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD5: return "BINDING_IN_TEXCOORD5";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD6: return "BINDING_IN_TEXCOORD6";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD7: return "BINDING_IN_TEXCOORD7";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD8: return "BINDING_IN_TEXCOORD8";
    case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD9: return "BINDING_IN_TEXCOORD9";
    default: UNREACHABLE();
    }
}

std::string  name(FRAGMENT_SHADER_OUTPUT_BINDING_LOCATION const  location)
{
    switch (location)
    {
    case FRAGMENT_SHADER_OUTPUT_BINDING_LOCATION::BINDING_OUT_COLOUR: return "BINDING_OUT_COLOUR";
    case FRAGMENT_SHADER_OUTPUT_BINDING_LOCATION::BINDING_OUT_TEXTURE_POSITION: return "BINDING_OUT_TEXTURE_POSITION";
    case FRAGMENT_SHADER_OUTPUT_BINDING_LOCATION::BINDING_OUT_TEXTURE_NORMAL: return "BINDING_OUT_TEXTURE_NORMAL";
    case FRAGMENT_SHADER_OUTPUT_BINDING_LOCATION::BINDING_OUT_TEXTURE_DIFFUSE: return "BINDING_OUT_TEXTURE_DIFFUSE";
    case FRAGMENT_SHADER_OUTPUT_BINDING_LOCATION::BINDING_OUT_TEXTURE_SPECULAR: return "BINDING_OUT_TEXTURE_SPECULAR";
    default: UNREACHABLE();
    }
}

std::string  name(FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME const  uniform_symbolic_name)
{
    switch (uniform_symbolic_name)
    {
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::TEXTURE_SAMPLER_DIFFUSE: return "TEXTURE_SAMPLER_DIFFUSE";
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::TEXTURE_SAMPLER_SPECULAR: return "TEXTURE_SAMPLER_SPECULAR";
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::TEXTURE_SAMPLER_NORMAL: return "TEXTURE_SAMPLER_NORMAL";
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::TEXTURE_SAMPLER_POSITION: return "TEXTURE_SAMPLER_POSITION";

    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::FOG_COLOUR: return "FOG_COLOUR";
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::AMBIENT_COLOUR: return "AMBIENT_COLOUR";
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::DIFFUSE_COLOUR: return "DIFFUSE_COLOUR";
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::SPECULAR_COLOUR: return "SPECULAR_COLOUR";

    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::DIRECTIONAL_LIGHT_DIRECTION: return "DIRECTIONAL_LIGHT_DIRECTION";
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::DIRECTIONAL_LIGHT_COLOUR: return "DIRECTIONAL_LIGHT_COLOUR";

    default: UNREACHABLE();
    }
}

bool  is_texture_sampler(FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME const  uniform_symbolic_name)
{
    switch (uniform_symbolic_name)
    {
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::TEXTURE_SAMPLER_DIFFUSE:
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::TEXTURE_SAMPLER_SPECULAR:
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::TEXTURE_SAMPLER_NORMAL:
    case FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME::TEXTURE_SAMPLER_POSITION:
        return true;
    default:
        return false;
    }
}

FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME  to_symbolic_uniform_name_of_fragment_shader(std::string  name)
{
    if (name.find("UNIFORM_") == 0UL)
        name = name.substr(std::strlen("UNIFORM_"));

    static std::unordered_map<std::string, FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME> const  map =
        []() -> std::unordered_map<std::string, FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME> {
            std::unordered_map<std::string, FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME> map;
            for (natural_32_bit i = 0U; i < num_FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAMEs(); ++i)
                map.insert({
                    qtgl::name(static_cast<FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME>(i)),
                    static_cast<FRAGMENT_SHADER_UNIFORM_SYMBOLIC_NAME>(i)
                    });
            return map;
        }();

    auto const  it = map.find(name);
    ASSUMPTION(it != map.cend());
    return it->second;
}


bool  compatible(std::unordered_set<VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION> const& vertex_program_output,
                 std::unordered_set<FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION> const& fragment_program_input)
{
    for (auto const  input : fragment_program_input)
        switch (input)
        {
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_POSITION :
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_POSITION) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_DIFFUSE  :
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_DIFFUSE) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_SPECULAR :
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_SPECULAR) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_NORMAL   :
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_NORMAL) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD0:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD0) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD1:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD1) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD2:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD2) == 0ULL)
                return false;;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD3:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD3) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD4:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD4) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD5:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD5) == 0ULL)
                return false;;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD6:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD6) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD7:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD7) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD8:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD8) == 0ULL)
                return false;
            break;
        case FRAGMENT_SHADER_INPUT_BUFFER_BINDING_LOCATION::BINDING_IN_TEXCOORD9:
            if (vertex_program_output.count(VERTEX_SHADER_OUTPUT_BUFFER_BINDING_LOCATION::BINDING_OUT_TEXCOORD9) == 0ULL)
                return false;
            break;
        default:
            UNREACHABLE();
        }
    return true;
}


}
