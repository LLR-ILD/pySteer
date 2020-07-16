################################################################################
#
#  Glue together the components of this folder/module. Adds the process of
#  writing the dictionaries to disk.
#
################################################################################
import json
import os

from .extract_from_cpp import marlin_processors_dict
from .processor_paths import load_local_processor_defaults
from .processor_paths import load_global_processor_defaults

# ------------------------------------------------------------------------------
# Functionality added by this file.
def json_name(stored_type):
    json_folder = "data"
    if stored_type == "project":
        return f"{json_folder}/project_processors.json"
    elif stored_type == "project descriptions":
        return f"{json_folder}/project_processors_descriptions.json"
    elif stored_type == "ilcsoft":
        return f"{json_folder}/ilcsoft_processors.json"
    elif stored_type == "ilcsoft descriptions":
        return f"{json_folder}/ilcsoft_processors_descriptions.json"
    else:
        raise Exception("`{}` is not a valid option!".format(stored_type))

def json_folder():
    """It is assumed that the name of the module that this function lives in is
    `pysteer`. Ideally, this module should reside inside the project.
    """
    module_name = "pysteer"
    path_to_module = __file__
    while True:
        if module_name == path_to_module[-len(module_name):]:
            break
        path_to_module, path_ending = os.path.split(path_to_module)
        if path_ending in ["/", ""]:
            print("\n{}.json_folder: It is expected that this funtion lives in "
                "a module called `{}`.Instead it is located in: \n"
                "    {}.".format(__name__, module_name, __file__))
            print("The files will instead be written from the location where "
                "this executing script is called from.")
            return ""
    return path_to_module

def write_jsons(type_prefix, processors_dict, descriptions_dict):
    processor_file = os.path.join(
        json_folder(), json_name(type_prefix))
    with open(processor_file, "w") as write_file:
        json.dump(processors_dict, write_file, indent=4, sort_keys=True)
    descriptions_file = os.path.join(
        json_folder(), json_name(type_prefix + " descriptions"))
    with open(descriptions_file, "w") as write_file:
        json.dump(descriptions_dict, write_file, indent=4, sort_keys=True)

# ------------------------------------------------------------------------------
# Main exposing functions for this folder.
def update_registered(
    confirm_ilcsoft_defaults=False,
    ilcsoft_path="/cvmfs/ilc.desy.de/sw/x86_64_gcc49_sl6/v02-00-02",
    local_paths=None,
    load_only=None,
    ):
    """For the description, see the docstring of the corresponding class method.
    """
    # (Re)build the project dict.
    local_files = load_local_processor_defaults(local_paths)
    local_processors, local_descriptions = marlin_processors_dict(
        local_files, return_descriptions=True, load_only=None)
    write_jsons("project", local_processors, local_descriptions)

    # Tackle the external ILCSoft/Marlin processors.
    if not confirm_ilcsoft_defaults:
        proc_file = os.path.join(json_folder(), json_name("ilcsoft"))
        if os.path.isfile(proc_file):
            with open(proc_file, "r") as read_file:
                ilcsoft_processors = json.load(read_file)
            if load_only:
                processor_names_in_dict = ilcsoft_processors.keys()
                for processor_name in load_only:
                    if processor_name not in processor_names_in_dict:
                        # A processor is missing. Thus, let's reload all.
                        confirm_ilcsoft_defaults = True
                        break
            else:
                confirm_ilcsoft_defaults = True
        else:
            # Since we can not find the dictionary file, we have to rebuild it.
            confirm_ilcsoft_defaults = True
    if confirm_ilcsoft_defaults:
        # Let's load the parameter defaults from Marlin (again).
        print("Build the parameter dict for the external Marlin processors "
            "from source files under:\n  {}.".format(ilcsoft_path))
        ilcsoft_files = load_global_processor_defaults(
            ilcsoft_path=ilcsoft_path)
        ilcsoft_processors, ilcsoft_descriptions = marlin_processors_dict(
            ilcsoft_files, return_descriptions=True, load_only=load_only)
        write_jsons("ilcsoft", ilcsoft_processors, ilcsoft_descriptions)

def processors_dict_from_json():
    """Load those processors dicts (with parameter dicts as values) previously
    saved in the json files back into one python dict.
    """
    processors_dict = {}
    read_jsons = [os.path.join(json_folder(), json_name(type_prefix))
        for type_prefix in ["ilcsoft", "project"]]
    for read_json in read_jsons:
        with open(read_json, "r") as read_file:
            processors_dict.update(json.load(read_file))
    return processors_dict