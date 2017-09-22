# -*- coding: utf-8 -*-

import os
import sys
import tempfile

from jinja2 import Template

import delegator

from .execlass import ExeClass


class Client(ExeClass):
    """Class for the GDB client that calls the flash functions."""

    def __init__(self, config=None):

        # Call the super's init.
        super().__init__()
        # Generate a temporary file to feed to gdb.
        _, self.cmd_file = tempfile.mkstemp(suffix=".txt", prefix="gdb_")

        self.debug = False

    @property
    def executable(self):
        """Executable path."""
        return os.path.join(self.config["S32"]["ROOT"],
                            "Cross_Tools",
                            self.config["CLIENT"]["PLATFORM"],
                            "bin",
                            self.config["CLIENT"]["EXE"])

    @property
    def cmd(self):
        """Command list to run."""
        return [self.executable,
                "--nx",
                "--command={}".format(self.cmd_file)]

    @property
    def template(self):
        """Jinja2 template class."""
        return Template(self.template_str)

    @property
    def template_str(self):
        """String of the gdb command template."""
        return """target remote 127.0.0.1:{{ port }}

set mem inaccessible-by-default off
set tcp auto-retry on
set tcp connect-timeout 240
set remotetimeout 60

monitor preserve1 0
monitor selectcore 0

set architecture powerpc:vle

{%- for elf in elfs %}
load "{{ elf }}"
{%- endfor %}

{%-if debug %}
continue
{% else %}
monitor _reset
quit
{% endif %}
"""

    def render(self, elfs):
        """Render the Jinja2 template to the temp file"""
        # Escape filenames for windows.
        print("DEBUG: {}".format(self.cmd_file))
        if sys.platform == "win32":
            elfs = [elf.replace("\\", "\\\\") for elf in elfs]
        with open(self.cmd_file, "w") as fid:
            print(
                self.template.render(
                    port=self.config["SERVER"]["SERVERPORT"],
                    debug=self.debug,
                    elfs=elfs),
                file=fid)

    def flash(self, elfs):
        """Run the flash command."""
        self.render(elfs)
        print("Waiting for GDB client to flash ...", end="")
        sys.stdout.flush()
        self.process = delegator.run(self.cmd, block=False)
        print("... Done")
        sys.stdout.flush()
        print(self.process.err)