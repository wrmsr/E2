import argparse
import os
import re


_template_CMakeLists_txt = \
"""set(THIS_TARGET_NAME <%TARGET_NAME%>)

<%QT_AUTOMOC%>

add_executable(${THIS_TARGET_NAME}
    program_info.hpp
    program_info.cpp

    program_options.hpp
    program_options.cpp

    main.cpp
    run.cpp
    )

target_link_libraries(${THIS_TARGET_NAME}
    <%LINK_LIBS_LIST%>
    ${BOOST_LIST_OF_LIBRARIES_TO_LINK_WITH}
    )

set_target_properties(${THIS_TARGET_NAME} PROPERTIES
    DEBUG_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Debug"
    RELEASE_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_Release"
    RELWITHDEBINFO_OUTPUT_NAME "${THIS_TARGET_NAME}_${CMAKE_SYSTEM_NAME}_RelWithDebInfo"
    )

install(TARGETS ${THIS_TARGET_NAME} DESTINATION "tests")

"""


_template_main_cpp = \
"""#include <<%TARGET_NAME%>/program_info.hpp>
#include <<%TARGET_NAME%>/program_options.hpp>
#include <utility/timeprof.hpp>
#include <utility/log.hpp>
#include <boost/filesystem.hpp>
#include <boost/filesystem/fstream.hpp>
#include <stdexcept>
#include <iostream>


LOG_INITIALISE(get_program_name() + "_LOG",true,true,warning)

extern void run(int argc, char* argv[]);

static void save_crash_report(std::string const& crash_message)
{
    std::cout << "ERROR: " << crash_message << "\\n";
    boost::filesystem::ofstream  ofile( get_program_name() + "_CRASH.txt", std::ios_base::app );
    ofile << crash_message << "\\n";
}

int main(int argc, char* argv[])
{
    try
    {
        initialise_program_options(argc,argv);
        if (get_program_options()->helpMode())
            std::cout << get_program_options();
        else if (get_program_options()->versionMode())
            std::cout << get_program_version() << "\\n";
        else
        {
            run(argc,argv);
            TMPROF_PRINT_TO_FILE(get_program_name() + "_TMPROF.html",true);
        }

    }
    catch(std::exception const& e)
    {
        try { save_crash_report(e.what()); } catch (...) {}
        return -1;
    }
    catch(...)
    {
        try { save_crash_report("Unknown exception was thrown."); } catch (...) {}
        return -2;
    }
    return 0;
}
"""


_template_program_info_hpp = \
"""#ifndef E2_TEST_<%TARGET_NAME_UPPER_CASE%>_PROGRAM_INFO_HPP_INCLUDED
#   define E2_TEST_<%TARGET_NAME_UPPER_CASE%>_PROGRAM_INFO_HPP_INCLUDED

#   include <string>

std::string  get_program_name();
std::string  get_program_version();
std::string  get_program_description();

#endif
"""


_template_program_info_cpp = \
"""#include <<%TARGET_NAME%>/program_info.hpp>

std::string  get_program_name()
{
    return "<%TARGET_NAME%>";
}

std::string  get_program_version()
{
    return "<%VERSION%>";
}

std::string  get_program_description()
{
    return "TODO: Specify here what library of E2 project is tested and what its\\n"
           "features are actually tested. (Note: end each line by '\\\\n'.)"
           ;
}
"""


_template_program_options_hpp = \
"""#ifndef E2_TEST_<%TARGET_NAME_UPPER_CASE%>_PROGRAM_OPTIONS_HPP_INCLUDED
#   define E2_TEST_<%TARGET_NAME_UPPER_CASE%>_PROGRAM_OPTIONS_HPP_INCLUDED

#   include <boost/program_options.hpp>
#   include <boost/noncopyable.hpp>
#   include <ostream>
#   include <memory>

class program_options : private boost::noncopyable
{
public:
    program_options(int argc, char* argv[]);

    bool helpMode() const { return vm.count("help") > 0; }
    bool versionMode() const { return vm.count("version") > 0; }

    // Add more option access/query functions here, if needed.

    std::ostream& operator<<(std::ostream& ostr) const;

private:
    boost::program_options::variables_map vm;
    boost::program_options::options_description desc;
};

typedef std::shared_ptr<program_options const> program_options_ptr;

void initialise_program_options(int argc, char* argv[]);
program_options_ptr get_program_options();

std::ostream& operator<<(std::ostream& ostr, program_options_ptr options);

#endif
"""


_template_program_options_cpp = \
"""#include <<%TARGET_NAME%>/program_options.hpp>
#include <<%TARGET_NAME%>/program_info.hpp>
#include <utility/assumptions.hpp>
#include <stdexcept>
#include <iostream>

program_options::program_options(int argc, char* argv[])
    : vm()
    , desc(get_program_description() + "\\nUsage")
{
    namespace bpo = boost::program_options;

    desc.add_options()
        ("help,h","Produces this help message.")
        ("version,v", "Prints the version string.")
        // Specify more options here, if needed.
        ;

    bpo::positional_options_description pos_desc;

    bpo::store(bpo::command_line_parser(argc,argv).allow_unregistered().
               options(desc).positional(pos_desc).run(),vm);
    bpo::notify(vm);
}

std::ostream& program_options::operator<<(std::ostream& ostr) const
{
    return ostr << desc;
}

static program_options_ptr  global_program_options;

void initialise_program_options(int argc, char* argv[])
{
    ASSUMPTION(!global_program_options.operator bool());
    global_program_options = program_options_ptr(new program_options(argc,argv));
}

program_options_ptr get_program_options()
{
    ASSUMPTION(global_program_options.operator bool());
    return global_program_options;
}

std::ostream& operator<<(std::ostream& ostr, program_options_ptr options)
{
    ASSUMPTION(options.operator bool());
    options->operator<<(ostr);
    return ostr;
}
"""


_template_run_cpp = \
"""#include <<%TARGET_NAME%>/program_info.hpp>
#include <<%TARGET_NAME%>/program_options.hpp>
#include <utility/test.hpp>
#include <utility/timeprof.hpp>
#include <utility/log.hpp>
#include <utility/basic_numeric_types.hpp>
#include <utility/assumptions.hpp>
#include <utility/invariants.hpp>


void run(int argc, char* argv[])
{
    TMPROF_BLOCK();

    TEST_PROGRESS_SHOW();

    // TODO: Implement your unit test here.
    //       Program options are already parsed. You
    //       thus do not have to access argc or argv.
    //       Simply call 'get_program_options()' to
    //       access the options.
    //       Further, call the macro:
    //              TEST_PROGRESS_UPDATE();
    //       each time you want to update the progress bar of your test.

    TEST_PROGRESS_HIDE();

    TEST_PRINT_STATISTICS();
}
"""


def parse_cmd_line():
    parser = argparse.ArgumentParser(
        description="This script allows you to easily create an initial version of source and build "
                    "files of a new unit test of some library of E2 project. The script contains a "
                    "'template test project' and it instantiates the template according to information "
                    "provided to this script via command line arguments. The script creates a new "
                    "sub-directory of the current directory and all generated files are stored into "
                    "that sub-directory. The name of the sub-directory is equal to a passed project name "
                    "(see the option '--target_name'). The project is automatically included into "
                    "the build of E2.")
    parser.add_argument("-T", "--target_name", type=str,
                        help="A project name of the test. All generated project files will be "
                             "generated into a newly created sub-directory of the current one. The"
                             "name of the sub-directory is equal as the passed target name.")
    parser.add_argument("-V","--version", type=str, default="0.01",
                        help="A string representing an initial version of the test. The version can be later "
                             "updated in a function 'get_program_version()' in a generated file 'program_info.cpp'")
    parser.add_argument("-L","--link_libs", nargs='+', type=str, default=["utility"],
                        help="A space-separated list of names of E2 libraries the test should be "
                             "linked with. Use quotes if library's name contains spaces. The library 'utility' "
                             "is always included automatically. Here is a list of poosible libraries: "
                             "netlab, netexp, netview, qtgl.\nNOTE: 3rd libraries must be added to the "
                             "CMakeLists.txt file of the tool manually. Only libraries Boost, Qt, and  "
                             "OpenGL are added automatically with E2 libraries dependent on them. "
                             "The Eigen 3rd library is header only.")
    args = parser.parse_args()
    return args


def scriptMain():
    args = parse_cmd_line()

    if args.target_name is None:
        print("ERROR: The option --target_name is not specified. Use the option --help for more info.")
        return
    if re.match(r"^[^\d\W]\w*\Z",args.target_name, re.UNICODE) is None:
        print("ERROR: The target name (i.e. the value of --target_name) is not an proper C identifier.")
        return
    dir_name = os.path.abspath("./" + args.target_name)
    if os.path.exists(dir_name):
        print("ERROR: The disk path '" + dir_name + "' already exists.")
        return
        
    add_qt = False
    add_gl = False
    libs_list = ""
    automoc_text = ""
    for libname in args.link_libs:
        if not libname in ["utility", "netlab", "netexp", "netview", "qtgl"]:
            print("ERROR: '" + libname + "' is not recognised as E2 library.")
            return
        if libname == "qtgl":
            add_qt = True
            add_gl = True
        libs_list += libname + "\n    "
    if "utility" not in args.link_libs:
        libs_list += "utility\n    "
    if add_qt:
        libs_list += "${QT5_LIST_OF_LIBRARIES_TO_LINK_WITH}" + "\n    "
        automoc_text = "set(CMAKE_AUTOMOC ON)\nset(CMAKE_CXX_FLAGS \"${CMAKE_CXX_FLAGS} ${QT5_CXX_FLAGS}\")"
    if add_gl:
        libs_list += "${OPENGL_LIST_OF_LIBRARIES_TO_LINK_WITH}" + "\n    "
    libs_list = libs_list.strip()

    os.mkdir(dir_name)

    out_file = open(dir_name + "/CMakeLists.txt","w")
    out_text = _template_CMakeLists_txt.replace("<%TARGET_NAME%>",args.target_name)\
                                       .replace("<%LINK_LIBS_LIST%>",libs_list)\
                                       .replace("<%QT_AUTOMOC%>",automoc_text)
    out_file.write(out_text)
    out_file.close()

    out_file = open(dir_name + "/main.cpp","w")
    out_text = _template_main_cpp.replace("<%TARGET_NAME%>",args.target_name)
    out_file.write(out_text)
    out_file.close()

    out_file = open(dir_name + "/program_info.hpp","w")
    out_text = _template_program_info_hpp.replace("<%TARGET_NAME_UPPER_CASE%>",args.target_name.upper())
    out_file.write(out_text)
    out_file.close()

    out_file = open(dir_name + "/program_info.cpp","w")
    out_text = _template_program_info_cpp.replace("<%TARGET_NAME%>",args.target_name)\
                                         .replace("<%VERSION%>",args.version)
    out_file.write(out_text)
    out_file.close()

    out_file = open(dir_name + "/program_options.hpp","w")
    out_text = _template_program_options_hpp.replace("<%TARGET_NAME_UPPER_CASE%>",args.target_name.upper())
    out_file.write(out_text)
    out_file.close()

    out_file = open(dir_name + "/program_options.cpp","w")
    out_text = _template_program_options_cpp.replace("<%TARGET_NAME%>",args.target_name)
    out_file.write(out_text)
    out_file.close()

    out_file = open(dir_name + "/run.cpp","w")
    out_text = _template_run_cpp.replace("<%TARGET_NAME%>",args.target_name)
    out_file.write(out_text)
    out_file.close()

    out_file = open("./CMakeLists.txt","a")
    out_file.write("\nadd_subdirectory(./" + args.target_name + ")\n    message(\"-- " + args.target_name + "\")\n")
    out_file.close()
    

if __name__ == "__main__":
    scriptMain()

