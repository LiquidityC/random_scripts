#!/usr/bin/env python

"""Handle multiple git repos that depend on each other"""

import os
import json
import sys
import getopt
import termstyle as sty

from git import Repo
from git import RemoteProgress

from pprint import pprint

KEY_PROJECTS = "projects"
KEY_WORKSPACE = "workspace_path"
CONFIG_FILENAME = "config.json"

VALID_PROJECTS = [
        # Setup default projects here
]

class ProgressPrinter(RemoteProgress):
    """Print progress of repo updates"""

    def __init__(self):
        super().__init__()
        self.total_steps = 20

    def update(self, op_code, cur_count, max_count=None, message=""):
        print("\r", end="")
        if not max_count and message != "done":
            print("    [", " " * self.total_steps, "] ", cur_count, " ", message, sep="", end="")
            return
        elif not max_count and message == "done":
            print("    [", "=" * self.total_steps, "] ", cur_count, " ", message, sep="")
            return

        step = max_count/self.total_steps
        steps = int(cur_count/step)
        remaining_steps = self.total_steps - steps
        print("    [", "=" * steps, ">" if remaining_steps > 0 else "",
              " " * (remaining_steps - 1), "]", sep="", end=" ")
        print(" ", cur_count, "/", max_count, sep="", end="")
        print(" ", message, end="", sep="")
        if cur_count == max_count:
            print("")

class Config:
    """Configuration handler"""

    def __init__(self, scriptfile):
        self.data = {}
        self.script_file = scriptfile

    def load(self):
        """Load a scriptfile"""

        if not os.path.isfile(script_file):
            return

        with open(self.script_file, "r") as fileobj:
            content = fileobj.read()
            if content:
                self.data = json.loads(content)

    def save(self):
        """Save configuration"""

        with open(self.script_file, "w") as fileobj:
            json.dump(self.data, fileobj, separators=(",", ": "), indent=4)

    def get(self, key):
        """Get config setting"""
        return self.data.get(key, "")

    def set(self, key, value):
        """Set a config setting"""
        self.data[key] = value

class ConfigLoader:
    """Config loader"""

    def __init__(self, script_file):
        self.script_file = script_file

    def __enter__(self):
        self.config = Config(self.script_file)
        self.config.load()
        self.__check_workspace()
        self.__check_projects()
        return self.config

    def __check_workspace(self):
        if not self.config.get(KEY_WORKSPACE):
            print("No workspace path configured!")
            print("Workspace path: ", end="")
            ws_path = input()
            self.config.set(KEY_WORKSPACE, ws_path)

    def __check_projects(self):
        if not self.config.get(KEY_PROJECTS):
            self.config.set(KEY_PROJECTS, VALID_PROJECTS)

    def __exit__(self, type, value, traceback):
        self.config.save()
        del self.config

class GitInterface:
    """Git interface"""

    def __init__(self, repo_list):
        self.repo_list = repo_list

    def __execute(self, cmd):
        for repo in self.repo_list:
            try:
                cmd(repo)
            except Exception as e:
                self.__print_exception(e)

    def __print_exception(self, e):
        print("  ", "%sFailed%s:" % (sty.red, sty.reset), e)

    def __any_repo_dirty(self):
        for repo in self.repo_list:
            if repo.is_dirty():
                print("%s%s is in dirty state %s" % (sty.red, repo.working_dir, sty.reset))
                return True
        return False

    def __dirty_check(self):
        if self.__any_repo_dirty():
            print("%sExiting...%s" % (sty.red, sty.reset))
            sys.exit(0)

    def stat_repos(self):
        print("%sPrinting status for all repos:%s" % (sty.green, sty.reset))
        def op(repo):
            if repo.is_dirty():
                print("--> %sDirty:%s %s %s(%s)%s" % (sty.red, sty.reset, repo.working_dir, sty.yellow, repo.active_branch, sty.reset))
            else:
                print("--> %sClean:%s %s %s(%s)%s" % (sty.green, sty.reset, repo.working_dir, sty.yellow, repo.active_branch, sty.reset))
        self.__execute(op)

    # This is pretty untested. Not sure if it works
    def review(self):
        self.__dirty_check()
        print("%sSubmitting repos not on master to review:%s" % (sty.green, sty.reset))
        def op(repo):
            if repo.active_branch.name != "master":
                print("--> %sSubmitting %s %s(%s)%s for review%s" % (sty.green, repo.working_dir, sty.yellow, repo.active_branch, sty.green, sty.reset))
                repo.git.review()
            else:
                print("--> %sIgnoring %s %s(%s)%s" % (sty.red, repo.working_dir, sty.yellow, repo.active_branch, sty.reset))
        self.__execute(op)

    def pull_repos(self):

        self.__dirty_check()
        print("%sPulling all repos%s" % (sty.green, sty.reset))
        def op(repo):
            print("--> %sPulling:%s %s" % (sty.green, sty.reset, repo.working_dir))
            repo.remotes.origin.pull(progress=ProgressPrinter())
        self.__execute(op)

    def fetch_repos(self):
        print("%sFetching all repos%s" % (sty.green, sty.reset))
        def op(repo):
            print("--> %sFetching:%s %s" % (sty.green, sty.reset, repo.working_dir))
            repo.remotes.origin.fetch(progress=ProgressPrinter())
        self.__execute(op)

    def delete_branch(self, branch):
        self.__dirty_check()
        print("%sDeleting branch %s in all repos%s" % (sty.green, branch, sty.reset))
        def op(repo):
            print("--> %sDeleting branch:%s %s in %s" % (sty.green, sty.reset, branch, repo.working_dir))
            repo.git.branch("-D", branch)
        self.__execute(op)

    def create_branch(self, branch):
        self.__dirty_check()
        print("%sCreating branch %s in all repos%s" % (sty.green, branch, sty.reset))
        def op(repo):
            print("--> %sCreating branch:%s %s in %s" % (sty.green, sty.reset, branch, repo.working_dir))
            repo.git.checkout('HEAD', b=branch)
        self.__execute(op)

    def create_branch_if_dirty(self, branch):
        print("%sCreating branch %s in dirty repos%s" % (sty.green, branch, sty.reset))
        def op(repo):
            if (repo.is_dirty()):
                print("--> %sCreating branch:%s %s in %s" % (sty.green, sty.reset, branch, repo.working_dir))
                repo.git.checkout('HEAD', b=branch)
        self.__execute(op)

    def stash(self):
        print("%sStashing dirty repos%s" % (sty.green, sty.reset))
        def op(repo):
            if (repo.is_dirty()):
                print("--> %sStashing repo: %s%s" % (sty.green, sty.reset, repo.working_dir))
                repo.git.stash()
        self.__execute(op)

    def checkout_branch(self, branch):
        self.__dirty_check()
        print("%sChecking out %s for all repos%s" % (sty.green, branch, sty.reset))
        def op(repo):
            print("--> %sChecking out:%s %s for %s" % (sty.green, sty.reset, branch, repo.working_dir))
            repo.git.checkout(branch)
        self.__execute(op)

    def create_tag(self, tag):
        self.__dirty_check()
        print("%sCreating tag '%s' in all repos%s" % (sty.green, tag, sty.reset))
        def op(repo):
            print("--> %sCreating tag:%s %s for %s" % (sty.green, sty.reset, tag, repo.working_dir))
            repo.create_tag(tag)
        self.__execute(op)

    def push_tag(self, tag):
        self.__dirty_check()
        print("%sPushing tag '%s' in all repos%s" % (sty.green, tag, sty.reset))
        def op(repo):
            print("--> %sPushing tag:%s %s for %s" % (sty.green, sty.reset, tag, repo.working_dir))
            repo.git.push("origin", "tag", tag)
        self.__execute(op)


def get_repo_list(ws_path):
    repos = []
    for item in os.listdir(ws_path):
        if os.path.isdir(os.path.join(ws_path, item)) and item in projects:
            repo_path = os.path.join(ws_path, item)
            repos.append(Repo(repo_path))
    return repos

def print_usage(include_description = False):
    if include_description:
        print("A toolk for managing all multiple related git projects from one command.")
        print("Supports: pulling, checking out tags/branches and creating branches and tags")
        print("You can chain commands by adding multiple flags as arguments")
        print("")
        print("Workspace and project settings are stored in config.json nexto source script")
        print("")
    print("Usage: %s [options]" % sys.argv[0])
    if include_description:
        print("")
        print("Examples:")
        print("    Pull current branch and create a new one")
        print("        %% %s -p -C <branch>" % sys.argv[0])
        print("    Pull current branch, checkout master, pull master, checkout other_branch, pull other_branch")
        print("        %% %s -p -c master -p -c other_branch -p" % sys.argv[0])
    print("")
    print("OPTIONS:")
    print("    -h,--help                            Print detailed instructions")
    print("    -c branch,--checkout=branch          Checkout a provided branch")
    print("    -C branch,--create=branch            Create provided branch")
    print("    -b branch,--create-if-dirty=branch   Create provided branch if repo is dirty")
    print("    -D branch,--delete=branch            Delete provided branch")
    print("    -r,--review                          Submit for review if branch != 'master' (beta)")
    print("    -t tag,--tag=tag                     Create tag locally")
    print("    -T tag,--remote-tag=tag              Create tag locally and remotely")
    print("    -s,--stat                            Check dirty status for repos")
    print("    -p,--pull                            Pull the repo")
    print("    -f,--fetch                           Fetch the repo")
    print("    -S,--stash                           Stash dirty repos")

def get_options():
    return ("rc:C:b:D:pfht:T:sS", [
        "review",
        "checkout=",
        "create=",
        "create-if-dirty=",
        "delete=",
        "pull",
        "fetch",
        "help",
        "tag=",
        "remote-tag=",
        "stat",
        "stash"
        ])

def parse_options(opts):
    if len(opts) < 1:
        print_usage()
        sys.exit(2)

    commands = []

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print_usage(True)
            sys.exit(0)
        elif opt in ("-c", "--checkout"):
            def cmd(git, arg):
                git.checkout_branch(arg)
        elif opt in ("-C", "--create"):
            def cmd(git, arg):
                git.create_branch(arg)
        elif opt in ("-b", "--create-if-dirty"):
            def cmd(git, arg):
                git.create_branch_if_dirty(arg)
        elif opt in ("-D", "--delete"):
            def cmd(git, arg):
                git.delete_branch(arg)
        elif opt in ("-s", "--stat"):
            def cmd(git, arg):
                git.stat_repos()
        elif opt in ("-p", "--pull"):
            def cmd(git, arg):
                git.pull_repos()
        elif opt in ("-f", "--fetch"):
            def cmd(git, arg):
                git.fetch_repos()
        elif opt in ("-t", "--tag"):
            def cmd(git, arg):
                git.create_tag(arg)
        elif opt in ("-r", "--review"):
            def cmd(git, arg):
                git.review()
        elif opt in ("-T", "--remote-tag"):
            def cmd(git, arg):
                git.create_tag(arg)
                git.push_tag(arg)
        elif opt in ("-S", "--stash"):
            def cmd(git, arg):
                git.stash();
        else:
            def cmd(git):
                print("Unknown operation %s(%s) requested" % (opt, arg))

        commands.append((cmd, arg))

    return commands

### SCRIPT START
if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.realpath(__file__))
    script_file = os.path.join(script_dir, CONFIG_FILENAME)

    try:
        opt_str, opt_list = get_options()
        opts, args = getopt.getopt(sys.argv[1:], opt_str, opt_list)
    except Exception:
        print_usage()
        sys.exit(2)

    commands = parse_options(opts)

    with ConfigLoader(script_file) as config:
        ws_path = config.get(KEY_WORKSPACE)
        projects = config.get(KEY_PROJECTS)

        print("%sConfigured workspace path:%s %s" % (sty.green, sty.reset, ws_path))
        git = GitInterface(get_repo_list(ws_path))

        for cmd in commands:
            cmd[0](git, cmd[1])

