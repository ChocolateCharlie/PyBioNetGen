import os, bionetgen, glob
from tempfile import TemporaryDirectory

from bionetgen.core.utils.logging import BNGLogger


class VisResult:
    def __init__(self, input_folder, name=None, vtype=None, app=None) -> None:
        self.app = app
        self.logger = BNGLogger(app=self.app)
        self.logger.debug(
            "Setting up VisResult object", loc=f"{__file__} : VisResult.__init__()"
        )
        self.input_folder = input_folder
        self.name = name
        self.vtype = vtype
        self.rc = None
        self.out = None
        self.files = []
        self.file_strs = {}
        self.file_graphs = {}
        self._load_files()

    def _load_files(self) -> None:
        self.logger.debug(
            "Loading graphml/gml files", loc=f"{__file__} : VisResult._load_files()"
        )
        # we need to assume some sort of GML output
        # at least for now
        # use the name, if given, search for GMLs if not
        gmls = glob.glob("*.gml")
        graphmls = glob.glob("*.graphml")
        graphfiles = gmls + graphmls
        for gfile in graphfiles:
            if self.name is None:
                self.files.append(gfile)
                # now load into string
                with open(gfile, "r") as f:
                    l = f.read()
                self.file_strs[gfile] = l
            else:
                # pull GMLs that contain the name
                if self.name in gfile:
                    self.files.append(gfile)
                    # now load into string
                    with open(gfile, "r") as f:
                        l = f.read()
                    self.file_strs[gfile] = l

    def _dump_files(self, folder) -> None:
        self.logger.debug(
            "Writing graphml/gml files", loc=f"{__file__} : VisResult._dump_files()"
        )
        os.chdir(folder)
        for gfile in self.files:
            g_name = os.path.split(gfile)[-1]
            with open(g_name, "w") as f:
                f.write(self.file_strs[gfile])


class BNGVisualize:
    def __init__(
        self, input_file, output=None, vtype=None, bngpath=None, suppress=None, app=None
    ) -> None:
        self.app = app
        self.logger = BNGLogger(app=self.app)
        self.logger.debug(
            "Setting up BNGVisualize object",
            loc=f"{__file__} : BNGVisualize.__init__()",
        )
        # set input, required
        self.input = input_file
        # set valid types
        self.valid_types = [
            "contactmap",
            "ruleviz_pattern",
            "ruleviz_operation",
            "regulatory",
        ]
        self.accept_types = [
            "contactmap",
            "ruleviz_pattern",
            "ruleviz_operation",
            "regulatory",
            "atom_rule",
            "all",
        ]
        # set visualization type, default yo contactmap
        if vtype is None or len(vtype) == 0:
            vtype = "contactmap"
        if vtype not in self.accept_types:
            raise ValueError(f"{vtype} is not a valid visualization type")

        self.vtype = vtype
        # set output
        self.output = output
        self.suppress = suppress
        self.bngpath = bngpath

    def run(self) -> VisResult:
        self.logger.debug("Running", loc=f"{__file__} : BNGVisualize.run()")
        return self._normal_mode()

    def _normal_mode(self):
        self.logger.debug(
            f"Running on normal mode, loading model {self.input}",
            loc=f"{__file__} : BNGVisualize._normal_mode()",
        )
        model = bionetgen.modelapi.bngmodel(self.input)
        model.actions.clear_actions()
        if self.vtype == "all":
            for valid_type in self.valid_types:
                model.add_action("visualize", action_args={"type": f"'{valid_type}'"})
        else:
            if self.vtype == "atom_rule":
                model.add_action("visualize", action_args={"type": f"'regulatory'"})
            else:
                model.add_action("visualize", action_args={"type": f"'{self.vtype}'"})
        # TODO: Work in temp folder
        cur_dir = os.getcwd()
        from bionetgen.core.main import BNGCLI

        self.logger.debug(
            "Generating visualization files",
            loc=f"{__file__} : BNGVisualize._normal_mode()",
        )

        if self.output is None:
            with TemporaryDirectory() as out:
                # instantiate a CLI object with the info
                cli = BNGCLI(model, out, self.bngpath, suppress=self.suppress)
                try:
                    cli.run()
                    # load vis
                    vis_res = VisResult(
                        os.path.abspath(os.getcwd()),
                        name=model.model_name,
                        vtype=self.vtype,
                    )
                    # go back
                    os.chdir(cur_dir)
                    # dump files
                    vis_res._dump_files(cur_dir)
                    return vis_res
                except Exception as e:
                    os.chdir(cur_dir)
                    print("Couldn't run the simulation, see error.")
                    raise e
        else:
            # instantiate a CLI object with the info
            cli = BNGCLI(model, self.output, self.bngpath, suppress=self.suppress)
            try:
                cli.run()
                # load vis
                vis_res = VisResult(
                    os.path.abspath(os.getcwd()),
                    name=model.model_name,
                    vtype=self.vtype,
                )
                # go back
                os.chdir(cur_dir)
                return vis_res
            except Exception as e:
                self.logger.error(
                    "Failed to run file",
                    loc=f"{__file__} : BNGVisualize._normal_mode()",
                )
                os.chdir(cur_dir)
                print("Couldn't run the simulation, see error.")
                raise e