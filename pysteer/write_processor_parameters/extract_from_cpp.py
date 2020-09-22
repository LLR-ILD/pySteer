################################################################################
#
#  Extract the Marlin  registered parameters from a specified (list of) .cpp
#  files with marlin_processors_dict. The other functions are helpers for this
#  one public function.
#
################################################################################
import re

# ------------------------------------------------------------------------------
# C++ parsing helper functions.
def remove_c_comments(text):
    """ Remove c-style comments.

    text: Blob of text with comments (can include newlines).
    returns: Text with comments removed.
    Found at:
        https://gist.github.com/ChunMinChang/88bfa5842396c1fbbc5b.
    """
    replacer = lambda match: (
        " " if match.group(0).startswith('/') else
        match.group(0)
    )
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)

def expression_end_position(code, char=";"):
    """Returns position of the first semicolon outside of a string.

    Assumes that there are no comments in the string!
    string in here refers to both strings (', ") and brackets {, (, [.
    """
    open_close = {"{": "}", "[": "]","(": ")",
        "'": "'", "\"": "\""}
    make_string_free_code = code
    string_char_count = 0
    while True:
        string_starts = [make_string_free_code.find(str_char)
                            for str_char in open_close.keys()]
        first_semicolon = make_string_free_code.find(char)
        if first_semicolon == -1:
            return -1
        if all([(first_semicolon <= x or x == -1)
                    for x in string_starts]):
            # There is a semicolon before any string starts or no semicolon.
            return first_semicolon + string_char_count
        if all([x == -1 for x in string_starts]): # There are no (more) strings.
            return first_semicolon + string_char_count
        # Remove the first string from the code.
        first_string_start = min([x for x in string_starts if x >= 0])
        open_str_char = make_string_free_code[first_string_start]

        # If the *string* is in fact a bracket, it can be nested.
        # We must make sure to remove the characters until the original bracket
        # is closed again (not e.g. a closing bracket character inside string).
        if open_str_char in "{[(":
            string_length = expression_end_position(
                make_string_free_code[first_string_start+1:],
                char=open_close[open_str_char]) + 2
        else:
            string_length = make_string_free_code[first_string_start+1:].find(
                open_close[open_str_char]) + 2
        if string_length == 1:
            # The string never ends. Thus, we did not find a semicolon.
            return -1
        string_char_count += string_length
        make_string_free_code = (make_string_free_code[:first_string_start]
            + make_string_free_code[first_string_start+string_length:])

def c_function_parameter_list(code, function_name):
    """Returns the list of function parameters of the first occurance of the
    funtion as well as the end position of this first occurance.

    Returns None object and position -1 if the function never occures.
    Assumes that there are no comments in the string!
    """
    function_begin = code.find(function_name)
    if function_begin == -1:
        return None, -1
    while code[function_begin+len(function_name)] not in " (":
        try_new_find = code[function_begin+1:].find(function_name)
        if try_new_find == -1:
            return None, -1
        function_begin += try_new_find + 1

    function = code[function_begin:]
    open_br = function.find("(")
    #close_br = function.rfind(")") # rfind: Last occurance.
    # Better than above line: The next line checks for first occurance of
    # closing bracket that is not inside another construct ("", '', [], {}, ()).
    close_br = open_br + 1 + expression_end_position(
        function[open_br+1:], char=")")
    if open_br == -1 or close_br == -1:
        return None, -1
    within_brackets = function[open_br+1:close_br]
    parameter_list = []
    comma_position = -1
    length_of_parameter = -1
    while length_of_parameter != 0:
        length_of_parameter = expression_end_position(
            within_brackets[comma_position+1:], char=",") + 1
        parameter_list.append(within_brackets[
            comma_position+1:comma_position+length_of_parameter])
        comma_position += length_of_parameter
    # The last list item is empty. Fill it with the content after the last char.
    parameter_list[-1] = within_brackets[comma_position+1:]
    for i, param in enumerate(parameter_list):
        parameter_list[i] = param.rstrip().lstrip()
    # Remove the last item if it is empty (trailing comma in code).
    if parameter_list[-1] == "":
        parameter_list.pop()
    return parameter_list, function_begin+close_br

def c_function_parameter_all_occurances(code, function_name):
    """Returns a  list of all the parameter lists for a functions occurance in
    the code. (Empty list for no occurance).

    Assumes that there are no comments in the string!
    """
    parameter_list_list = []
    remaining_code = code
    while True:
        parameter_list, start = c_function_parameter_list(
            remaining_code, function_name)
        remaining_code = remaining_code[start:]
        if parameter_list:
            parameter_list_list.append((parameter_list))
        else:
            break
    return parameter_list_list


def old_cpp_value_parser(value):
    if value[-1] == "f":
        return value[:-1]
    for cpp_phrase in ["std::string(", "bool(", "double(", "int(", "float(",
                       "string("]:
        if cpp_phrase in value and value[-1] == ")":
            value = value.replace(cpp_phrase, "")[:-1]
    return value


def cpp_value_parser(value, is_string_mode=False):
    """Strip some common cpp decorators. E.g.
    5.0f -> 5.0, std::string("abc") -> "abc"

    is_string_mode: Simplifies the processor name search.
    """
    stringInsidePythonString = lambda val: val[0] in "'\"" and val[0] == val[-1]

    # Value as first condition: value=None possible after previous strips.
    cleaned_value = old_cpp_value_parser(value)
    if cleaned_value and stringInsidePythonString(cleaned_value):
        cleaned_value = cleaned_value[1:-1]
        if is_string_mode:
            return (cleaned_value, True)
        else:
            return cleaned_value
    if is_string_mode:
        return cleaned_value, False
    else:
        return cleaned_value

# ------------------------------------------------------------------------------
# Helper functions that are only interesting in Marlin/ILCSoft context.
def marlin_register_dict(code):
    """Create a dict of the registered parameters and collections of a Marlin
    processor (ILCSoft).

    Assumes that there are no comments in the string!
    """
    # For other things we might want to specify. E.g. lcioInType, type.
    description_dict = {}
    param_dict = {}
    processor_parameters = c_function_parameter_all_occurances(
        code, function_name="registerProcessorParameter")
    #for parameters in processor_parameters:
    #    if len(parameters) != 4: # [name, description, cpp_var_name, value]
    #        raise Exception("Unexpected number of parameters ({} instead of 4)."
    #            " They are:\n  ".format(len(parameters))
    #            + "\n  ".join([str(p) for p in parameters]))
    #    name = parameters[0]
    #    description = parameters[1]
    #    value = cpp_value_parser(parameters[3])
    #    description_dict[name] = description
    #    param_dict[name] = dict(value=value)

    opt_processor_parameters = c_function_parameter_all_occurances(
        code, function_name="registerOptionalParameter")
    if opt_processor_parameters:
        processor_parameters.extend(opt_processor_parameters)
    for parameters in processor_parameters:
        if len(parameters) == 5:
            if ".size()" in parameters[4]:
                # It is possible to give C++ vector objects as a parameter, by
                # defining them inside the file. As I do not see how this could
                # be done from the steering file, we should ignore these
                # parameters when building the dict.
                continue
        # [name, description, cpp_var_name, value]
        # or [name, description, cpp_var_name, value, size]
        if len(parameters) not in [4, 5]:
            raise Exception("Unexpected number of parameters ({} instead of 4 "
                "or 5). They are:\n  ".format(len(parameters))
                + "\n  ".join([str(p) for p in parameters]))
        name = cpp_value_parser(parameters[0])
        description = cpp_value_parser(parameters[1])
        value = cpp_value_parser(parameters[3])
        #size = parameters[4]
        description_dict[name] = description
        param_dict[name] = dict(value=value)

    processor_parameters = c_function_parameter_all_occurances(
        code, function_name="registerInputCollection")
    for parameters in processor_parameters:
        # [lcioInType, name, description, cpp_var_name, value]
        if len(parameters) != 5:
            raise Exception("Unexpected number of parameters ({} instead of 5)."
                " They are:\n  ".format(len(parameters))
                + "\n  ".join([str(p) for p in parameters]))
        lcioInType = cpp_value_parser(parameters[0])
        name = cpp_value_parser(parameters[1])
        description = cpp_value_parser(parameters[2])
        value = cpp_value_parser(parameters[4])
        description_dict[name] = description
        param_dict[name] = dict(value=value, lcioInType=lcioInType)

    processor_parameters = c_function_parameter_all_occurances(
        code, function_name="registerOutputCollection")
    for parameters in processor_parameters:
        # [lcioOutType, name, description, cpp_var_name, value]
        if len(parameters) != 5:
            raise Exception("Unexpected number of parameters ({} instead of 5)."
                " They are:\n  ".format(len(parameters))
                + "\n  ".join([str(p) for p in parameters]))
        lcioOutType = cpp_value_parser(parameters[0])
        name = cpp_value_parser(parameters[1])
        description = cpp_value_parser(parameters[2])
        value = cpp_value_parser(parameters[4])
        description_dict[name] = description
        param_dict[name] = dict(value=value, lcioOutType=lcioOutType)

    return param_dict, description_dict


def getProcessorName(comment_free_cc):
    """This more involved approach became necessary when finding out that the
    LCIOOutProcessor had the following line

    >>> LCIOOutputProcessor::LCIOOutputProcessor(const std::string& typeName) : Processor(typeName),

    before the targetted
    >>> LCIOOutputProcessor::LCIOOutputProcessor() : Processor("LCIOOutputProcessor"),

    Ergo, it is necessary to look for all occurances of the Processor keyphrase,
    and only string-type variables can be what we are looking for.
    """
    getOutOfList = lambda l: l[0]

    for processor_name_keyphrase in [
        "marlin::Processor",  # Keyphrase after which the name is defined.
        " Processor",         # The marlin namespace might have been used.
    ]:
        processor_name_candidates = c_function_parameter_all_occurances(
                comment_free_cc, processor_name_keyphrase)
        for candidate in processor_name_candidates:
            name, is_string = cpp_value_parser(getOutOfList(candidate),
                                               is_string_mode=True)
            if is_string:
                return name, True

    return "", False


# ------------------------------------------------------------------------------
# The main function of this file.
def marlin_processors_dict(look_at_list, return_descriptions=False,
    load_only=None):
    """From a list of .cpp file names, extract their Marlin processor
    parameters.

    Gives a dict where each entry is a dict of the parameters for a specific
    processor.
    This per-parameter dict has information about the name of the parameter, its
    default value and, if applicable, its lcioIn/lcioOut collection type.
    The descriptions of the parameters can be returned in an additional dict.
    : param look_at_list (list[string]): The .cpp file locations.
    : param return_descriptions (bool): default=False.
    : param load_only (None|list[str]): If None, load all processors.
        Else, put only those processors into the dict that are inside this list.
    """
    param_dict = {}
    descriptions_dict = {}
    for cc_file_name in look_at_list:
        #print(cc_file_name)
        # Using latin-1 as encoding instead of python3's standard utf-8:
        # It turns out some of the ILCSoft files contain non-utf8 bytes in their
        # comments, leading to an UnicodeDecodeError.
        with open(cc_file_name, "r", encoding="latin-1") as file:
            comment_free_cc = remove_c_comments(file.read())
        processor_name, name_was_found = getProcessorName(comment_free_cc)
        if not name_was_found:
            continue
        if load_only and (processor_name not in load_only):
            continue

        param_1proc, descriptions_1proc = marlin_register_dict(comment_free_cc)
        param_dict[processor_name] = param_1proc
        descriptions_dict[processor_name] = descriptions_1proc
    if load_only:
        for load_processor in load_only:
            if load_processor not in param_dict.keys():
                print("The processor {}\n  was not found. Maybe the name was "
                "mis-spelled, or the processor_search_paths were not broad "
                "enough.".format(load_processor))
    if return_descriptions:
        return param_dict, descriptions_dict
    else:
        return param_dict
