import requests, json, datetime, pytz
import os, re, collections
import click

ENDPOINT = "https://api.clockify.me/api/v1"
VERBOSE = False
config_file = os.path.expanduser("~/.clockify.cfg")
CONFIG = {
    "api": "",
    "uid": "",
    "username": "",
    "wid": "",
    "workspace": "",
    "pid": "",
    "project": "",
    "timezone": "",
}
headers = {"X-Api-Key": None}


def set_api(api):
    headers["X-Api-Key"] = api

def get_workspaces():
    r = requests.get(f"{ENDPOINT}/workspaces", headers=headers)
    return {workspace["name"]: workspace["id"] for workspace in r.json()}

def get_projects(workspace=None):
    workspaceId = get_workspaceId(workspace)
    r = requests.get(f"{ENDPOINT}/workspaces/{workspaceId}/projects", headers=headers)
    return {project["name"]: project["id"] for project in r.json()}

def print_json(inputjson):
    click.echo(json.dumps(inputjson, indent=2))

def get_timezone_offset_string():
    return datetime.datetime.now(pytz.timezone(CONFIG['timezone'])).strftime('%z')

def get_time_format(time: datetime.datetime = None):
    timediff = pytz.timezone(CONFIG["timezone"]).utcoffset(datetime.datetime.now())
    if time:
        return (time - timediff).strftime('%Y-%m-%dT%H:%M:%SZ')
    return (datetime.datetime.now() - timediff).strftime('%Y-%m-%dT%H:%M:%SZ')

def start_time_entry(
    workspace=None, description=None, billable="false", project=None, tags=None
):
    start = get_time_format()
    workspaceId = get_workspaceId(workspace)
    projectId = get_projectId(project)
    body = {
        "start": start,
        "billable": billable,
        "description": description,
        "projectId": projectId,
        "taskId": None,
        "tagIds": tags,
    }
    if VERBOSE:
        print('body:')
        print(body)
    r = requests.post(
        f"{ENDPOINT}/workspaces/{workspaceId}/time-entries", headers=headers, json=body
    )
    return r.json(), r.status_code

def check_duration_format(duration: str):
    format = r"^\d{1,2}$|^\d{1,2}:\d{1,2}$|^\d{1,2}:\d{1,2}:\d{1,2}$"
    match = re.match(format, duration)
    if match:
        hms = list(map(lambda i: int(i), duration.split(":")))
        if len(hms) == 1:
            hms = [hms[0], 0, 0]
        if len(hms) == 2:
            hms = [hms[0], hms[1], 0]
        if hms[1] > 59 or hms[2] > 59:
            print("Incorrect minute or second format (too high)")
            quit()
        return hms
    else:
        print(
            "Incorrect duration format. Must be with one or two digits h/hh -> h:m:s | h:m | h"
        )
        quit()

def add_time_entry(
    duration: str,
    workspace=None,
    description=None,
    billable="false",
    project=None,
    tags=None,
):
    end = datetime.datetime.now()
    hms = check_duration_format(duration)
    start = end - datetime.timedelta(hours=hms[0], minutes=hms[1], seconds=hms[2])
    workspaceId = get_workspaceId(workspace)
    body = {
        "start": get_time_format(start),
        "end": get_time_format(end),
        "billable": billable,
        "description": description,
        "projectId": get_projectId(project),
        "taskId": None,
        "tagIds": tags,
    }
    r = requests.post(
        f"{ENDPOINT}/workspaces/{workspaceId}/time-entries", headers=headers, json=body
    )
    return r.json(), r.status_code, start

def get_in_progress(workspace):
    workspaceId = get_workspaceId(workspace)
    r = requests.get(
        f"{ENDPOINT}/workspaces/{workspaceId}/user/{CONFIG['uid']}/time-entries?in-progress=true",
        headers=headers,
    )
    if r.status_code != 200:
        click.echo(
            f"Failed to get time entry in progress with status code {r.status_code}"
        )
        quit()
    json = r.json()
    if json == []:
        click.echo("No entry in progress")
        quit()
    else:
        return json[0]

def finish_time_entry(workspace):
    current = get_in_progress(workspace)
    current_id = current["id"]
    workspaceId = get_workspaceId()
    body = {
        "start": current["timeInterval"]["start"],
        "billable": current["billable"],
        "description": current["description"],
        "projectId": current["projectId"],
        "taskId": current["taskId"],
        "tagIds": current["tagIds"],
        "end": get_time_format(),
    }
    r = requests.put(
        f"{ENDPOINT}/workspaces/{workspaceId}/time-entries/{current_id}",
        headers=headers,
        json=body,
    )
    return r.json(), r.status_code

def get_time_entries(workspace=None):
    workspaceId = get_workspaceId(workspace)
    r = requests.get(
        f"{ENDPOINT}/workspaces/{workspaceId}/user/{CONFIG['uid']}/time-entries",
        headers=headers,
    )
    return r.json()[:10]

def remove_time_entry(tid, workspace=None):
    workspaceId = get_workspaceId(workspace)
    r = requests.delete(
        f"{ENDPOINT}/workspaces/{workspaceId}/time-entries/{tid}", headers=headers
    )
    return r

def get_workspaceId(workspace=None):
    if workspace:
        workspaceId = get_workspaces()[workspace]
    else:
        if CONFIG["wid"] != "":
            workspaceId = CONFIG["wid"]
        else:
            return set_workspace()[1]
    return workspaceId

def set_workspace(workspace=None):
    if not workspace:
        workspace = click.prompt("Workspace name")
    workspaceId = get_workspaces()[workspace]
    CONFIG["wid"] = workspaceId
    CONFIG["workspace"] = workspace
    # Save config
    with open(config_file, "w") as f:
        json.dump(CONFIG, f)

    return workspace, workspaceId

def get_projectId(project=None):
    if project:
        projectId = get_projects()[project]
    else:
        if CONFIG["pid"] != "":
            projectId = CONFIG["pid"]
        else:
            return set_project()[1]
    return projectId

def set_project(project=None):
    if not project:
        project = click.prompt("Project name")
    projectId = get_projects()[project]
    CONFIG["pid"] = projectId
    CONFIG["project"] = project
    # Save config
    with open(config_file, "w") as f:
        json.dump(CONFIG, f)

    return project, projectId

def get_user():
    r = requests.get(f"{ENDPOINT}/user", headers=headers)
    return r.json()

# Commands

class OrderedGroup(click.Group): # For commands to custom ordered.
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or collections.OrderedDict()

    def list_commands(self, ctx):
        return self.commands

@click.group(cls=OrderedGroup)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose):
    "A command line interface for the time tracker app Clockify."
    global CONFIG
    global VERBOSE
    VERBOSE = verbose

    if os.path.exists(config_file):
        with open(config_file) as f:
            CONFIG = json.load(f)
            set_api(CONFIG["api"])
    else:
        api = click.prompt("Your API key (see bottom of user settings on the webpage)")
        CONFIG["api"] = api
        set_api(api)
        user = get_user()
        CONFIG["uid"] = user["id"]
        CONFIG["username"] = user["name"]
        CONFIG["timezone"] = user["settings"]["timeZone"]
        with open(config_file, "w") as f:
            json.dump(CONFIG, f)


@click.command("start", short_help="Start a new time entry")
@click.option("-d", "--description", type=str, default=None, help="Entry description")
@click.option("-w", "--workspace", "workspace", type=str, default=None)
@click.option(
    "--billable", is_flag=True, default=False, help="Set if entry is billable"
)
@click.option("--project", "-p", default=None, help="Project ID")
@click.option("--tag", "-g", multiple=True, help="Multiple tags permitted")
def start(workspace, description, billable, project, tag):
    ret, status = start_time_entry(workspace, description, billable, project, list(tag))
    if status == 201:
        click.echo(
            f'Started timer for {CONFIG["username"]} on Workspace: {CONFIG["workspace"]} with Project: {CONFIG["project"]}'
        )
    else:
        click.echo(f"Failed to start timer with status {status}")
    if VERBOSE:
        print_json(ret)


@click.command("finish", short_help="Finish an on-going time entry")
@click.option("-w", "--workspace", "workspace", type=str, default=None)
def finish(workspace):
    ret, status = finish_time_entry(workspace)
    if status == 200:
        click.echo(
            f'Finished timer for {CONFIG["username"]} on Workspace: {CONFIG["workspace"]} with Project: {CONFIG["project"]}' +\
            f' with Duration: {re.sub("PT", "", ret["timeInterval"]["duration"])}'
        )
    if VERBOSE:
        print_json(ret)


@click.command("user", short_help="Get user information")
def user():
    user = get_user()
    if VERBOSE:
        print_json(user)
    click.echo(f"{user['id']}: {user['name']}")


@click.command("projects", short_help="Show all projects")
@click.option("-w", "--workspace", "workspace", type=str, default=None)
def projects(workspace):
    data = get_projects(workspace)
    if VERBOSE:
        print_json(data)
    else:
        for name in data:
            id = data[name]
            click.echo(f"{id}: {name}")


@click.command("workspaces", short_help="Show all workspaces")
def workspaces():
    data = get_workspaces()
    if VERBOSE:
        print_json(data)
    else:
        for name in data:
            id = data[name]
            click.echo(f"{id}: {name}")


@click.command("set_workspace", short_help="Set the default workspace")
@click.argument("workspace", type=str)
def s_workspace(workspace):
    name, wid = set_workspace(workspace)
    click.echo(f"Default workspace set to: {name}, {wid}")

@click.command("set_project", short_help="Set the default project")
@click.argument("project", type=str)
def s_project(project):
    name, pid = set_project(project)
    click.echo(f"Default project set to: {name}, {pid}")


@click.command("entries", short_help="Show previous 10 time entries")
@click.option(
    "-w",
    "--workspace",
    "workspace",
    type=str,
    default=None,
    help="Default is set with set_workspace",
)
@click.option("-i", "--info", "info", is_flag="True")
def entries(workspace, info):
    data = get_time_entries(workspace)
    if VERBOSE:
        print_json(data)
    else:
        for entry in data:
            mes = (
                f"Start: {entry['timeInterval']['start']}{get_timezone_offset_string()}, "
                + f"Duration: {re.sub('PT', '', entry['timeInterval']['duration'])}"
            )
            if info:
                mes += (
                    f", Description: {entry['description']}, "
                    + f"End: {entry['timeInterval']['end']}{get_timezone_offset_string()}, "
                    + f"ID: {entry['id']}"
                )
            click.echo(mes)


@click.command("entry", short_help="Add entry with duration")
@click.argument("duration", type=str)
@click.option(
    "-w",
    "--workspace",
    "workspace",
    type=str,
    default=None,
    help="Default is set with set_workspace",
)
@click.option("-d", "--description", type=str, default=None, help="Entry description")
@click.option(
    "-b", "--billable", is_flag=True, default=False, help="Set if entry is billable"
)
@click.option("--project", "-p", default=None, help="Project ID")
@click.option("--tag", "-t", multiple=True, help="Multiple tags permitted")
@click.option("-i", "--info", "info", is_flag="True")
def add(workspace, duration, description, billable, project, tag, info):
    ret, status, start = add_time_entry(duration, workspace, description, billable, project, list(tag))
    if status == 201:
        click.echo(f'Successfully added time entry with start {start.strftime("%d/%b/%Y")} and duration {duration}.')
        if info:
            click.echo( f'User: {CONFIG["username"]}, Workspace: {CONFIG["workspace"]}, Project: {CONFIG["project"]}.')
    else:
        click.echo(f"Failed time entry with status {status}")
    if VERBOSE:
        print_json(ret)


@click.command("remove_entry", short_help="Remove entry")
@click.argument("timeEntryId")
@click.option("-w", "--workspace", "workspace", type=str, default=None)
def remove_entry(timeentryid, workspace):
    ret = remove_time_entry(timeentryid, workspace)
    if ret.ok:
        click.echo(f"Removed entry {timeentryid}")
    else:
        click.echo( f"Failed to remove entry {timeentryid} with status {ret.status_code}")


@click.command("in-progress", short_help="Get timer in progress")
@click.option("-w", "--workspace", "workspace", type=str, default=None)
def in_progress(workspace):
    ret = get_in_progress(workspace)
    duration = datetime.datetime.now(tz=pytz.timezone(CONFIG['timezone'])) - datetime.datetime.strptime(f"{ret['timeInterval']['start']}+0000", '%Y-%m-%dT%H:%M:%SZ%z') 
    click.echo(f"Current time entry: {ret['id']} started {ret['timeInterval']['start']}{get_timezone_offset_string()}, Duration: {str(duration)}")
    if VERBOSE:
        print_json(ret)


cli.add_command(start)
cli.add_command(finish)
cli.add_command(add)
cli.add_command(entries)
cli.add_command(projects)
cli.add_command(workspaces)
cli.add_command(s_workspace)
cli.add_command(s_project)
cli.add_command(user)
cli.add_command(remove_entry)
cli.add_command(in_progress)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
