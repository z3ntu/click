#! /usr/bin/python3

# Copyright (C) 2013 Canonical Ltd.
# Author: Brian Murray <brian@ubuntu.com>

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

"""Use and manage a Click chroot."""

from __future__ import print_function

from argparse import ArgumentParser, REMAINDER

from click.chroot import ClickChroot


def create(args):
    ClickChroot("saucy", args.architecture,
                "ubuntu-sdk-13.10").create()


def install(args):
    packages = args.packages
    ClickChroot("saucy", args.architecture,
                "ubuntu-sdk-13.10").install(*packages)


def destroy(args):
    # ask for confirmation?
    ClickChroot("saucy", args.architecture,
                "ubuntu-sdk-13.10").destroy()


def execute(args):
    # not sure what to do wrt setting up the env
    program = args.program
    ClickChroot("saucy", args.architecture,
                "ubuntu-sdk-13.10").run(*program)


def upgrade(args):
    ClickChroot("saucy", args.architecture,
                "ubuntu-sdk-13.10").upgrade()


def run(argv):
    parser = ArgumentParser("click chroot")
    subparsers = parser.add_subparsers(
        description="management subcommands",
        help="valid commands")
    parser.add_argument(
        "-a", "--architecture", required=True,
        help="architecture for the chroot")
    create_parser = subparsers.add_parser(
        "create",
        help="create a chroot of the provided architecture")
    create_parser.set_defaults(func=create)
    destroy_parser = subparsers.add_parser(
        "destroy",
        help="destroy the chroot")
    destroy_parser.set_defaults(func=destroy)
    upgrade_parser = subparsers.add_parser(
        "upgrade",
        help="upgrade the chroot")
    upgrade_parser.set_defaults(func=upgrade)
    install_parser = subparsers.add_parser(
        "install",
        help="install packages in the chroot")
    install_parser.add_argument(
        "packages", nargs="+",
        help="packages to install")
    install_parser.set_defaults(func=install)
    execute_parser = subparsers.add_parser(
        "run",
        help="run a program in the chroot")
    execute_parser.add_argument(
        "program", nargs=REMAINDER,
        help="program to run with arguments")
    execute_parser.set_defaults(func=execute)
    args = parser.parse_args(argv)
    args.func(args)
