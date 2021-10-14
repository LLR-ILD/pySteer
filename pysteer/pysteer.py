################################################################################
#
#  Class definition file for Pysteer.
#
################################################################################
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys
from .marlin_global import lcio_file_dict, MarlinGlobal
from .marlin_xml import write_steering_file, xml_string
from .write_processor_parameters import (
    update_registered, processors_dict_from_json)

class Pysteer(object):
    """Interface for the creation of Marlin steering files.

    It does not seem necessary to alter the defaults of `lcio_file_dict` in this
    project, so this is not included in the interface. Ig needed, this could be
    done explicitely by changing self.lcio_dict.
    : param change_parameter_defaults (dict[dict]): Dict of the same form of
        the processors dicts. Those processors specified will have the dicts
        of those parameters that are specified replaced by the given parameter
        dicts.
    : param confirm_ilcsoft_defaults (bool): If false, the dict of external
        processor parameter information is only updated if a processor is
        requested that is not yet in the dict.
    : param ilcsoft_path (str): Location from which Marlin will be run.
    : param ilcsoft_processors (list[str]|None): Defines which (external) Marlin
        processors this class should know about. If None is chosen, all
        processors available in the chosen Marlin version will be available, for
        the price of reduced clarity.
    : param marlin_global (MarlinGlobal): The MarlinGlobal object is used to set
        the parameters in the <global/> section of the steering file. If None is
        given, a default MarlinGlobal object will be used. Parameters can still
        be changed later on by directly altering the MarlinGlobal object that
        is called by pysteer_object.marlin_global.
    : param set_parameter_value (dict[str]): In contrast, to above
        change_parameter_defaults, this dict takes param-name: param-value as
        dict items. The parameter's value will be changed in every processor
        that the parameter appears in. Es this is more generic, it is executed
        before change_parameter_defaults.
    """
    def __init__(
        self,
        change_parameter_defaults={},
        confirm_ilcsoft_defaults=False,
        ilcsoft_path="/cvmfs/ilc.desy.de/sw/x86_64_gcc49_sl6/v02-00-02",
        ilcsoft_processors=[
            "InitializeDD4hep",
            "IsolatedLeptonTaggingProcessor",
        ],
        local_project_paths=None,
        marlin_global=None,
        set_parameter_value={},
    ):
        import sys
        print(sys.argv[0])
        self.change_parameter_defaults = change_parameter_defaults
        self.confirm_ilcsoft_defaults = confirm_ilcsoft_defaults
        self.execute_processors = [] # List filled with processor-dicts that
            # will be executed in this order.
        if type(marlin_global) != MarlinGlobal:
            self.marlin_global = MarlinGlobal()
        else:
            self.marlin_global =  marlin_global
        self.ilcsoft_path = ilcsoft_path
        self.ilcsoft_processors = ilcsoft_processors
        self.local_project_paths = local_project_paths
        self.lcio_dict = lcio_file_dict()
        self.processors_dict = {}
        self.set_parameter_value = set_parameter_value

        self.update_processors()

    # --------------------------------------------------------------------------
    # Load the processor parameter defaults.
    def update_processors(self, confirm_ilcsoft_defaults=None):
        """Get the .json files in `pysteer` that store information on the
        default values of project and external Marlin processors up-to-date.

        : param confirm_ilcsoft_defaults (bool|None): By default (if None), the
            value set for the object (self.) is used.
            If false, the dict of external processor parameter information is
            only updated if a processor is requested that is not yet in the
            dict.
        """
        if confirm_ilcsoft_defaults == None:
            confirm_ilcsoft_defaults=self.confirm_ilcsoft_defaults
        update_registered(
            confirm_ilcsoft_defaults=confirm_ilcsoft_defaults,
            ilcsoft_path=self.ilcsoft_path,
            local_paths=self.local_project_paths,
            load_only=self.ilcsoft_processors,
        )
        self.processors_dict = processors_dict_from_json()
        # Change the disk-written information in memory.
        # Incorporate self.set_parameter_value.
        for parameter in self.set_parameter_value:
            for processor in self.processors_dict.values():
                if parameter in processor.keys():
                    value = self.set_parameter_value[parameter]
                    processor[parameter]["value"] = value
        # Incorporate self.change_parameter_defaults.
        for proc_name, param_dicts in self.change_parameter_defaults.items():
            if proc_name not in self.processors_dict.keys():
                print("A change of default parameters was requested for the "
                    "processor `{}`. This pocessor is unknown. No defaults are "
                    "changed.".format(proc_name))
                continue
            keys_to_pop = []
            for param_name in param_dicts.keys():
                if param_name not in self.processors_dict[proc_name].keys():
                    print("The parameter `{}` is not recognized for the "
                        "processor `{}`. It will be ignored.".format(
                            param_name, proc_name))
                else:
                    if (hasattr(param_dicts[param_name], "keys")
                    and "value" in param_dicts[param_name].keys()):
                        self.processors_dict[proc_name][param_name].update(
                            param_dicts[param_name])
                    else:
                        print("Updating the default value for the parameter "
                            "`{}` of processor `{}` was not successfull. \n"
                            "It is necessary to pass a dict that knows the key "
                            "`value`. Given: ".format(param_name, proc_name))
                        print(param_dicts[param_name])

    def full_update(self):
        """Rebuild the processor default parameter dictionaries.

        Equivalent to self.update_processors() if
        self.confirm_ilcsoft_defaults=True.
        """
        self.update_processors(confirm_ilcsoft_defaults=True)

    # --------------------------------------------------------------------------.
    def add(self, name, changed_params={}):
        """Define which processors should be envoked. This adds the specified
        processor as the last processor that will be called by Marlin.

        : param name (str): Name of the processor.
        : param changed_params (dict[dict]): Change those parameters for which
            the default should not be used. Should be of the form:
            {"param_to_change": dict(value="new_value), "next_change": ...}.
        """
        if name not in self.processors_dict.keys():
            print(self.processors_dict.keys())
            raise Exception("The above processors are known. A processor named "
                "`{}` was requested but could not be found.".format(name))
        self.execute_processors.append((name, changed_params))

    # --------------------------------------------------------------------------
    def write(self, xml_name):
        """Produce a steering file from the state of the pysteer object.

        : param xml_name (str): Name of the produced steering file.
        """
        global_dict = self.marlin_global.as_dict()
        write_steering_file(self.execute_processors, global_dict,
            self.processors_dict, xml_name)

    def __str__(self):
        global_dict = self.marlin_global.as_dict()
        return xml_string(
            self.execute_processors, global_dict, self.processors_dict)

    # --------------------------------------------------------------------------
    def _get_process_name(self, process):
        return process

    def run(self, batch_mode=True, debug_process="Pe3e3h", pols=None,
        batch_processes=None, n_process_iterations=1):
        """Actually do the analysis by calling Marlin on a steering file.

        : param batch_mode (bool): If true (default), and if a batch system is
            found on the machine, the jobs are sent to the batch system.
            Else, the job is directly run on the machine. In this case, only
            the process `debug_process` is used.
        : debug_process (str): The process that is used if no batch system is
            used/found.
        : param pols (list[str]): The default (None) uses all polarisations.
            Else only the specified polarisations are used.
        : param batch_processes (list[str]): By default (None), all process
            files are used. To restrict the analysis to specific processes, fill
            this list.
            For a more fine grained control, pass a dict. The key functions as
            both the job name and the folder name. The dict value now must be
            a list of the lcio file paths.
            This parameter is only used if batch_mode == True.
        """
        def make_folder():
            now = datetime.now()
            run_dir = Path.home() / Path(now.strftime("%Y-%m-%d-%H%M%S"))
            run_dir.mkdir()
            steering_py = sys.argv[0]
            shutil.copyfile(steering_py, run_dir / "steerer.py")
            return run_dir

        def make_files(files, process_dir, process, cmd_template):
            self.marlin_global.LCIOInputFiles = ("\n          ".join(files)
                + "\n     ")
            steer_name = process + ".xml"
            log_name = "log_" + steer_name.rstrip(".xml") + ".txt"
            self.write(process_dir / steer_name)
            cmd = cmd_template.format(steer_name, log_name)
            if shutil.which("Marlin") is None:
                print("`Marlin` is not available in this environment.")
                print("A steering file was nonetheless written into "
                    f"{process_dir}.")
                return

            # TODO: Get rid of security-flawed shell=True.
            subprocess.call(cmd, cwd=process_dir, shell=True)

        run_dir = make_folder()
        if batch_mode:
            if shutil.which("bsub") is not None:
                cmd_template = "bsub -q s -J JOBNAME 'Marlin {} &> {} 2>&1'"
            else:
                cmd_template = "Marlin {} &> {} 2>&1"
            if type(batch_processes) == dict:
                # This (dict) should be viewed as a legacy option (only).
                if n_process_iterations != 1:
                    raise Exception("type(batch_processes) == dict, but "
                        f"{n_process_iterations=} != 1. You can't use both!")
                for folder, files in batch_processes.items():
                    cmd_t = cmd_template.replace("JOBNAME", folder)
                    files = [f for f in files if Path(f).exists()]
                    process_dir = run_dir / folder
                    process_dir.mkdir(parents=True, exist_ok=True)
                    make_files(files, process_dir, folder,
                        cmd_template=cmd_t)
            else:
                for pol, processes_dict in self.lcio_dict.items():
                    if pols and pol in pols:
                        continue
                    for process, files in processes_dict.items():
                        if batch_processes and process not in batch_processes:
                            continue
                        for i in range(n_process_iterations):
                            max_per_job = self.marlin_global.MaxRecordNumber
                            self.marlin_global.SkipNEvents = i * max_per_job
                            if n_process_iterations == 1:
                                it_id = ""
                            else:
                                if max_per_job == -1:
                                    raise Exception("MaxRecordNumber = -1 and "
                                        f"{n_process_iterations=} != 1?")
                                it_id = f"_{i:02}"
                            process_name = self._get_process_name(process)
                            job_name = f"{pol}_{process_name}{it_id}"
                            cmd_t = cmd_template.replace("JOBNAME",
                                                         job_name)
                            process_dir = run_dir / pol / f"{process_name}{it_id}"
                            process_dir.mkdir(parents=True, exist_ok=True)
                            make_files(files, process_dir, process_name,
                                cmd_template=cmd_t)
        else:
            cmd_template = "Marlin {} &> {} 2>&1"
            if not pols:
                pols = self.lcio_dict.keys()
            if not isinstance(debug_process, str):
                if len(debug_process) == 2:
                    debug_process, files = debug_process
                else:
                    raise Exception(f"{debug_process=}")
            else:
                files = [""]
                for pol in pols:
                    if self.lcio_dict[pol].get(debug_process):
                        files.extend(self.lcio_dict[pol].get(debug_process))
            make_files(files, process_dir=run_dir, process=debug_process,
                cmd_template=cmd_template)
