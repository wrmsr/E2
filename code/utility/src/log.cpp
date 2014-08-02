#include <utility/log.hpp>
#include <utility/assumptions.hpp>
#include <boost/log/utility/setup/file.hpp>
#include <boost/log/attributes/clock.hpp>
#include <boost/log/attributes/current_thread_id.hpp>
#include <boost/chrono.hpp>
#include <boost/filesystem/fstream.hpp>
#include <vector>
#include <iostream>
#include <sstream>
#include <ctime>

static bool LOG_SETUP(std::string const& log_file_name)
{
    static bool first_call = true;
    if (!first_call)
    {
        LOG(info,"LOG_SETUP was already called ==> ignoring this call.");
        return false;
    }
    first_call = false;

    boost::log::core::get()->add_global_attribute("TimeStamp",boost::log::attributes::local_clock());
    boost::log::core::get()->add_global_attribute("ThreadID",boost::log::attributes::current_thread_id());

    namespace expr = boost::log::expressions;
    boost::log::add_file_log(
        boost::log::keywords::file_name = log_file_name,
        boost::log::keywords::auto_flush = true,
        boost::log::keywords::open_mode = (std::ios::out | std::ios::app),
        boost::log::keywords::format = //"[%TimeStamp%][%ThreadID%][%File%][%Line%][%Level%]: %Message%"
            "    <tr>\n"
            "        <td>%TimeStamp%</td>\n"
            "        <td>%ThreadID%</td>\n"
            "        <td>%File%</td>\n"
            "        <td>%Line%</td>\n"
            "        <td>%Level%</td>\n"
            "        <td>%Message%</td>\n"
            "    </tr>\n"
    );

    return true;
}

std::string const& logging_severity_level_name(logging_severity_level const level)
{
    static std::vector<std::string> level_names{ "debug", "info", "warning", "error" };
    ASSUMPTION(static_cast<unsigned int>(level) < level_names.size());
    return level_names.at(static_cast<unsigned int>(level));
}

static std::string get_timestamp()
{
    std::time_t t = boost::chrono::system_clock::to_time_t(boost::chrono::system_clock::now());
    std::tm* const ptm = std::localtime(&t);
    std::stringstream sstr;
    sstr << "--"
         << ptm->tm_year + 1900 << "-"
         << ptm->tm_mon << "-"
         << ptm->tm_mday << "--"
         << ptm->tm_hour << "-"
         << ptm->tm_min << "-"
         << ptm->tm_sec
         ;
    return sstr.str();
}

static std::string filename_with_timestamp(boost::filesystem::path const& log_file_name)
{
    boost::filesystem::path path = log_file_name.branch_path();
    boost::filesystem::path name = log_file_name.filename().replace_extension("");
    boost::filesystem::path ext = log_file_name.extension();
    return (path / (name.string() + get_timestamp() + ext.string())).string();
}

logging_setup_caller::logging_setup_caller(std::string const& log_file_name,
                                           bool const add_creation_timestamp_to_filename,
                                           bool const add_default_file_extension)
    : m_log_file_name(
        [](std::string const& log_file_name, bool const add_creation_timestamp_to_filename,
                                             bool const add_default_file_extension)
        {
            std::string const file_name = log_file_name + (add_default_file_extension ? ".html" : "");
            return add_creation_timestamp_to_filename ? filename_with_timestamp(file_name) : file_name;
        }(log_file_name,add_creation_timestamp_to_filename,add_default_file_extension)
        )
{
    boost::filesystem::ofstream f(m_log_file_name);
    f << "<!DOCTYPE html>\n"
         "<html>\n"
         "<head>\n"
         "    <meta charset=\"UTF-8\">\n"
         "    <title>LOG-FILE: " << log_file_name << "</title>\n"
         "    <style type=\"text/css\">\n"
         "        body\n"
         "        {\n"
         "            font-family:arial;\n"
         "            font-size:10px;\n"
         "        }\n"
         "        table,th,td\n"
         "        {\n"
         "            border:1px solid black;\n"
         "            border-collapse:collapse;\n"
         "        }\n"
//         "        th,td\n"
//         "        {\n"
//         "            padding:5px;\n"
//         "        }\n"
//         "        th\n"
//         "        {\n"
//         "            text-align:left;\n"
//         "        }\n"
         "   </style>\n"
         "</head>\n"
         "<body>\n"
//         "    <table style=\"width:300px\">\n"
         "    <table>\n"
         "    <tr>\n"
         "        <th>Time stamp</th>\n"
         "        <th>Thread ID</th>\n"
         "        <th>File</th>\n"
         "        <th>Line</th>\n"
         "        <th>Level</th>\n"
         "        <th>Message</th>\n"
         "    </tr>\n"
         ;
    LOG_SETUP(m_log_file_name);
}

logging_setup_caller::~logging_setup_caller()
{
    boost::log::core::get()->remove_all_sinks();
    boost::filesystem::ofstream f(m_log_file_name,std::ios::out | std::ios::app);
    f << "    </table>\n"
         "</body>\n"
         "</html>\n"
         ;
}
