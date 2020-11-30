################################################################################
#
#  A mini-class for conveniently changing the <global/> section of a Marlin
#  steering file build with the pysteer class.
#
################################################################################
import collections
import os
import pathlib

default_simulation_path_starts = [
    "/grid_mnt/data__DATA/data.polcalice/data/flc/kunath/Data_SM",  # polui/LLR
    "/group/ilc/soft/samples/mc-dbd/ild/dst-merged/250-TDR_ws",  # KEK
    "/home/kunath/iLCSoft/data/SM", # Laptop
    "/group/ilc/grid/storm/prod/ilc/mc-2020/ild/dst-merged/250-SetA", # KEK new.
]
default_machine = "E250-TDR_ws"

def lcio_file_dict(
    simulation_path_starts=None,
    exclude=["Pffh_mumu"], require=[], machine=default_machine):
    """Build a dictionary of the .slcio file locations.

    Some changes to the code would be necessary if we ever need to include
    photon initial states.
    : param path_starts (list[str]): Specify one or multiple strings. The dict
        will be build using files found under these locations.
    : param exclude (list[str]): Strings that are not allowed in a file location
        or name.
    : param require(list[str]): Strings that all must be part of the path/ file
        name.
    : param machine(str): Machine name as specified in the .slcio file.
    """
    if simulation_path_starts is None:
        simulation_path_starts = default_simulation_path_starts
    polarisations = ["eLpR", "eLpL", "eRpL", "eRpR"]
    full_files_dict = {pol: dict() for pol in polarisations}
    for path_start_str in simulation_path_starts:
        files_dict = {}
        for pol in polarisations:
            files_dict[pol] = collections.defaultdict(list)
        path_start = pathlib.Path(path_start_str)
        if not path_start.exists():
            continue
        candidate_paths = path_start.rglob("*.slcio")
        for path in candidate_paths:
            path = str(path)
            skip_path = False
            for excl in exclude:
                if excl in path:
                    skip_path = True
                    break
            for req in require:
                if req not in path:
                    skip_path = True
                    break
            if skip_path:
                continue
            # reconstruction_version.simulation_version.detector_model. \
            # production_machine.process_id.process_name.e_pol-p_pol---.slcio
            # Where --- differ between the MC runs.
            prod_machine, _, process, e_pol, p_pol = path.split(".")[3:8]
            pol = e_pol + p_pol[:2]
            if prod_machine != machine or pol not in polarisations:
                continue
            files_dict[pol][process].append(path)
        [full_files_dict[pol].update(files_dict[pol]) for pol in polarisations]
    if sum([len(d) for d in full_files_dict.values()]) == 0:
        ex_txt = ("No matching `.slcio` process files were found in any of the "
            "subdirectories of:\n   "
                           + ",\n   ".join(simulation_path_starts) + ".")
        if machine != default_machine:
            ex_txt = (f"{ex_txt}\nMaybe your chosen ILC machine option's "
                      f"data set is not available locally? {machine=}.")
        raise FileNotFoundError(ex_txt)
    return full_files_dict


class MarlinGlobal(object):
    """Object that stores the information for the <global/> section.
    Most likely LCIOInputFiles will have to be changed.

    If specifying process does not give the wished for result, try building the
    object and then directly changing LCIOInputFiles.
    : param MaxRecordNumber (int|str): If 0, all available events are used.
        Else, stop after MaxRecordNumber events. Default=0
    : param SkipNEvents (int|str):  Default=0
    : param Verbosity (str): Valid options: DEBUG0-4, MESSAGE0-4, WARNING0-4,
        ERROR0-4,SILENT. Default=MESSAGE.
    : param process (str): Name of the process that the .slcio files should
        contain. To not complicate the interface to much, the default parameters
        of `lcio_file_dict` are used. In most use cases the value of
        `LCIOInputFiles` set at start time should anyways just be a placeholder.
    """
    def __init__(
        self,
        MaxRecordNumber=0,
        SkipNEvents=0,
        Verbosity="MESSAGE",
        process = "Pe1e1h",
        **lcio_dict_kw,
    ):
        self.MaxRecordNumber = MaxRecordNumber
        self.SkipNEvents = SkipNEvents
        self.Verbosity = Verbosity

        lcio_dict = lcio_file_dict(**lcio_dict_kw)
        lcio_processes = []
        for pol_dict in lcio_dict.values():
            lcio_processes.extend(pol_dict.keys())
        if process not in lcio_processes:
            process = lcio_processes[0]
        process_files = [""]
        for pol in lcio_dict.keys():
            process_files.extend(lcio_dict[pol].get(process))
        LCIOInputFiles = "\n          ".join(process_files) + "\n     "
        self.LCIOInputFiles = LCIOInputFiles

    def as_dict(self):
        """Build a python dict version of the global information.
        """
        global_dict = dict(
            LCIOInputFiles = dict(value=self.LCIOInputFiles),
            MaxRecordNumber = dict(value=self.MaxRecordNumber),
            SkipNEvents = dict(value=self.SkipNEvents),
            Verbosity = dict(value=self.Verbosity,
                options="DEBUG0-4,MESSAGE0-4,WARNING0-4,ERROR0-4,SILENT"),
        )
        return global_dict

    def __str__(self):
        gl_print = ["A MarlinGlobal object with values:"]
        for param, value in self.__dict__.items():
            gl_print.append("{}: {}".format(param, value))
        return "\n  ".join(gl_print)
