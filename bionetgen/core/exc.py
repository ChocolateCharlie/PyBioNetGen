class BioNetGenError(Exception):
    """Base class for all PyBNG exceptions."""

    pass


class BioNetGenVersionError(Exception):
    """Error related to mismatching required PyBNG."""

    def __init__(self, cur_version, req_version):
        self.message = f"Your PyBNG version: {cur_version} doesn't match required version: {req_version}. Try updating PyBNG with `pip install bionetgen --upgrade`"
        self.cur_version = cur_version
        self.req_version = req_version
        super().__init__(self.message)


class BNGParseError(BioNetGenError):
    """Error related to parsing a BNGL file."""

    def __init__(
        self, bngl_path=None, message="There was an issue with parsing your BNGL file"
    ):
        self.path = bngl_path
        full_msg = f"There was an issue parsing BNGL file: {bngl_path}"
        if message is not None:
            full_msg += message
        self.message = full_msg
        super().__init__(self.message)


class BNGFileError(BioNetGenError):
    """Error related to the BNGL file."""

    def __init__(self, bngl_path, message="There was an issue with your BNGL file"):
        self.path = bngl_path
        self.message = message
        super().__init__(self.message)


class BNGModelError(BioNetGenError):
    """Error related to the BNG model object."""

    def __init__(self, model, message="There was an issue with your BNG model"):
        self.model = model
        full_msg = f"There was an issue with BNGL model: {self.model}\n"
        if message is not None:
            full_msg += message
        self.message = full_msg
        super().__init__(self.message)


class BNGRunError(BioNetGenError):
    """Error related to running BNG2.pl."""

    def __init__(
        self,
        command,
        message="There was an issue with running BNG2.pl. There might be an issue with your model and please make sure perl is installed",
        stdout=None,
        stderr=None,
    ):
        self.command = command
        self.stdout = stdout
        self.stderr = stderr
        full_msg = f"Tried to run command: {command}\n"
        full_msg += message + "\n"
        full_msg += f"Stdout was: {stdout}\n"
        full_msg += f"Stderr was: {stderr}\n"
        self.message = full_msg
        super().__init__(self.message)


class BNGCompileError(BioNetGenError):
    """Error related to compiling C/Py file of BNG model."""

    def __init__(
        self,
        model,
        message="There was an issue compiling your BNG model, please make sure your bionetgen.conf file points to a compiled CVODE 2.6.0",
    ):
        self.model = model
        self.message = message
        super().__init__(self.message)
