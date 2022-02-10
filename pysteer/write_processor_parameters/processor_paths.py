################################################################################
#
#  Collect all the file names of the .cpp files defining a Marlin::processor.
#  This is a combination of two tasks:
#   1. Find the processors in the current project.
#   2. For the global processor, decide for a Marlin(Reco) version and define
#      which of the available processors you want to include.
#
################################################################################
import os
import pathlib

# ------------------------------------------------------------------------------
# 0. Common components.
def cpp_sources_in_paths(processor_search_paths):
    candidate_processor_files = []
    for path_to_processors in processor_search_paths:
        for pattern in ["*.c", "*.cc", "*.cpp"]:
            candidate_processor_files.extend(
                pathlib.Path(path_to_processors).rglob(pattern))
    return candidate_processor_files

# ------------------------------------------------------------------------------
# 1. Local processors.
def load_local_processor_defaults(processor_search_paths=None):
    """A few assumptions are implicitely made about the structure of the file
    system. See the print statement inside this function.
    """
    if processor_search_paths is not None:
        return cpp_sources_in_paths(processor_search_paths)

    processors_folder = "processors"
    path_to_processors = __file__
    while True:
        path_to_processors, path_ending = os.path.split(path_to_processors)
        if processors_folder in os.listdir(path_to_processors):
            break
        elif path_ending in ["/", ""]:
            print("\n{}.load_local_processor_defaults: It is expected that a "
                "folder called `{}` can be found in one of the ancestor "
                "directories of this functions location.\n"
                "The function is located in: \n"
                "    {}.".format(__name__, processors_folder, __file__))
            print("Therefore no local processors are registered with pysteer.")
            return []
    processor_search_paths = [
        os.path.join(path_to_processors, processors_folder)
    ]
    return cpp_sources_in_paths(processor_search_paths)

# ------------------------------------------------------------------------------
# 2. Global ILCSoft processors.
default_ilcsoft_path = "/cvmfs/ilc.desy.de/sw/x86_64_gcc82_centos7/v02-02-03"

def load_global_processor_defaults(
    ilcsoft_path=default_ilcsoft_path,
    ):
    """

    : param ilcsoft_path (str): There is some (weak) dependence on the ILCSoft
        version: The files and their defaults might have changed.
        The dependence is weak, as processors should be carried over from older
        versions anyways. Thus, as long as a recent ILCSoft version is chosen
        we should be fine.
    """
    processor_search_paths = [os.path.join(ilcsoft_path, folder)
        for folder in [
            #"MarlinDD4hep",
            #"MarlinReco",
            "", # The full ILCSoft suit.
        ]
    ]
    return cpp_sources_in_paths(processor_search_paths)