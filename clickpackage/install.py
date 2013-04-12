# Copyright (C) 2013 Canonical Ltd.
# Author: Colin Watson <cjwatson@ubuntu.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Installing Click packages."""

from __future__ import print_function

__metaclass__ = type

import inspect
import os
import subprocess

from debian.debfile import DebFile
from debian.debian_support import Version

from clickpackage.preinst import static_preinst
from clickpackage.versions import base_version, spec_version


CLICK_VERSION = "0.1"


class ClickInstaller:
    def __init__(self, root):
        self.root = root

    def _preload_path(self):
        if "CLICK_PACKAGE_PRELOAD" in os.environ:
            return os.environ["CLICK_PACKAGE_PRELOAD"]
        my_path = inspect.getsourcefile(ClickInstaller)
        preload = os.path.join(
            os.path.dirname(my_path), os.pardir, "preload",
            "libclickpreload.so")
        if os.path.exists(preload):
            return os.path.abspath(preload)
        # TODO: unhardcode path
        return "/usr/lib/click-package/libclickpreload.so"

    def audit_control(self, control_part):
        control_fields = control_part.debcontrol()

        try:
            package = control_fields["Package"]
        except KeyError:
            raise ValueError("No Package field")
        # TODO: perhaps just do full name validation?
        if "/" in package:
            raise ValueError("Invalid character '/' in Package: %s" % package)

        try:
            click_version = Version(control_fields["Click-Version"])
        except KeyError:
            raise ValueError("No Click-Version field")
        if click_version > spec_version:
            raise ValueError(
                "Click-Version: %s newer than maximum supported version %s" %
                (click_version, spec_version))

        try:
            click_base_system = Version(control_fields["click-base-system"])
        except KeyError:
            raise ValueError("No Click-Base-System field")
        if click_base_system > base_version:
            raise ValueError(
                "Click-Base-System: %s newer than current version %s" %
                (click_base_system, base_version))

        for field in (
            "Pre-Depends", "Depends", "Recommends", "Suggests", "Enhances",
            "Conflicts", "Breaks",
            "Provides",
        ):
            if field in control_fields:
                raise ValueError(
                    "%s field is forbidden in Click packages" % field)

        scripts = control_part.scripts()
        if ("preinst" in scripts and
                scripts["preinst"] == static_preinst.encode()):
            scripts.pop("preinst", None)
        if scripts:
            raise ValueError(
                "Maintainer scripts are forbidden in Click packages "
                "(found: %s)" %
                " ".join(sorted(scripts)))

    def audit(self, package):
        self.audit_control(package.control)

    def install(self, path):
        package = DebFile(filename=path)
        try:
            self.audit(package)

            # TODO: avoid instantiating debcontrol twice
            inst_dir = os.path.join(
                self.root, package.debcontrol()["Package"])
            assert os.path.dirname(inst_dir) == self.root
        finally:
            package.close()

        admin_dir = os.path.join(inst_dir, ".click")
        if not os.path.exists(admin_dir):
            os.makedirs(admin_dir)
            with open(os.path.join(admin_dir, "available"), "w"):
                pass
            with open(os.path.join(admin_dir, "status"), "w"):
                pass
            os.mkdir(os.path.join(admin_dir, "info"))
            os.mkdir(os.path.join(admin_dir, "updates"))
            os.mkdir(os.path.join(admin_dir, "triggers"))

        command = [
            "dpkg",
            "--force-not-root",
            "--instdir", inst_dir,
            "--admindir", os.path.join(inst_dir, ".click"),
            "--path-exclude", "/.click/*",
            "--log", os.path.join(self.root, ".click.log"),
            # TODO: --status-fd etc. integration?
            "--no-triggers",
            "--install", path,
        ]
        env = dict(os.environ)
        env["LD_PRELOAD"] = self._preload_path()
        subprocess.check_call(command, env=env)
