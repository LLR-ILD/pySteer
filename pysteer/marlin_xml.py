################################################################################
#
#  Write the Marlin xml steering file from the collected information.
#
################################################################################
from datetime import datetime

def xml_parameters(default_dict, changes_dict={}):
    param_strings = []
    for parameter_name, parameter_dict in sorted(default_dict.items()):
        if (parameter_name in changes_dict
        and changes_dict[parameter_name]["value"] != parameter_dict["value"]):
            parameter_dict = changes_dict[parameter_name]
            indent = "    "
        else: # Indent the default parameters differently.
            indent = "      "
        param_line = indent + "<parameter name={}".format(parameter_name)
        for attr in parameter_dict:
            if attr == "value": continue
            param_line += " {tag}={value}".format(
                tag=attr, value=parameter_dict[attr])
        param_line += "> {} </parameter>".format(parameter_dict["value"])
        param_strings.append(param_line)
    return "\n".join(param_strings)

def xml_string(execute_processors, global_dict, project_defaults):
    """Same as `write_steering_file`, but returns the string instead of writing
    it to a file.
    """
    now = datetime.now()
    header_comment = ("<!-- This steering file was produced via a python script"
      " with pysteer {}.-->\n\n".format(now.strftime("%d/%m/%Y-%H:%M:%S")))
    xml_pieces = []
    xml_pieces.append(header_comment)
    xml_pieces.append("<marlin>\n\n  <execute>\n")
    called_processor_types = list(list(zip(*execute_processors))[0])
    called_processor_names = []
    for i, processor_type in enumerate(called_processor_types):
        name = processor_type+"_{:03}".format(i)
        called_processor_names.append(name)
        xml_pieces.append("    <processor name=\"{}\"/>\n".format(name))
    xml_pieces.append("  </execute>\n\n  <global>\n")
    xml_pieces.append(xml_parameters(global_dict))
    xml_pieces.append("\n  </global>\n\n")
    # The per-processor part.
    for name, proc in zip(called_processor_names, execute_processors):
        proc_type, proc_dict = proc
        header = "  <processor name={} type={}>\n".format(name, proc_type)
        xml_pieces.append(header)
        xml_pieces.append(xml_parameters(
            default_dict=project_defaults[proc_type],
            changes_dict=proc_dict
        ))
        xml_pieces.append("\n  </processor>\n\n")
    xml_pieces.append("</marlin>")
    xml_content = "".join(xml_pieces)
    return xml_content

def write_steering_file(execute_processors, global_dict, project_defaults,
    xml_name="steering.xml"):
    """Produce an xml file that can be fed into Marlin.

    : param execute_processors (list[tuple]): The first tuple element should be
        the name of a Marlin processor. The second (and last) element should be
        a dict with those parameters that we want to alter wrt the defaults (can
        be an empty dict).
    : param global_dict (dict[dict]): Used to set the parameters in the
        <global/> section of the xml file.
    : param project_defaults (dict[dict]): For each of the processors that can
        be called in the project, have the paramaters and their default values
        in this dict.
    : param xml_name (str): Name of the produced steering file.
    """
    xml_content = xml_string(execute_processors, global_dict, project_defaults)
    with open(xml_name, "w") as write_file:
        write_file.write(xml_content)