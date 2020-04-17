import requests, json, datetime
import os, re
import click

ENDPOINT = "https://api.clockify.me/api/v1"
VERBOSE = False
CLOCKIFY_API_EMAIL = os.environ["CLOCKIFY_API_EMAIL"]
CLOCKIFY_API_PASSWORD = os.environ["CLOCKIFY_API_PASSWORD"]
config_file = os.path.expanduser("~/.clockify.cfg")
CONFIG = {"api": "", "uid": "", "wid": "", "workspace": ""}
headers = {"X-Api-Key": None}


def set_api(api):
    headers["X-Api-Key"] = api


def get_token():
    body = {"email": CLOCKIFY_API_EMAIL, "password": CLOCKIFY_API_PASSWORD}
    r = requests.post(ENDPOINT + "auth/token", headers=headers, json=body)
    return r.json()


def get_workspaces():
    r = requests.get(f"{ENDPOINT}/workspaces", headers=headers)
    return {workspace["name"]: workspace["id"] for workspace in r.json()}


def get_projects(workspace=None):
    workspaceId = get_workspaceId(workspace)
    r = requests.get(f"{ENDPOINT}/workspaces/{workspaceId}/projects", headers=headers)
    return {project["name"]: project["id"] for project in r.json()}


def print_json(inputjson):
    click.echo(json.dumps(inputjson, indent=2))


def get_current_time():
    return str(datetime.datetime.now().isoformat()) + "Z"


def start_time_entry(
    workspace=None, description=None, billable="false", project=None, tags=None
):
    start = get_current_time()
    workspaceId = get_workspaceId(workspace)
    body = {
        "start": start,
        "billable": billable,
        "description": description,
        "projectId": project,
        "taskId": None,
        "tagIds": tag,
    }
    r = requests.post(
        f"{ENDPOINT}/workspaces/{workspaceId}/time-entries", headers=headers, json=body
    )
    return r.json()


def check_duration_format(duration: str):
    format = r"(\d{2}:?(\d{2})?:?(\d{2})?)"
    print(re.match(format, duration))


def add_time_entry(
    duration: str,
    workspace=None,
    description=None,
    billable="false",
    project=None,
    tags=None,
):
    start = get_current_time()
    hms = duration.split(":")
    end = start + datetime.timedelta()
    workspaceId = get_workspaceId(workspace)
    body = {
        "start": start,
        "billable": billable,
        "description": description,
        "projectId": project,
        "taskId": None,
        "tagIds": tag,
    }
    # r = requests.post(
    #     f"{ENDPOINT}/workspaces/{workspaceId}/time-entries", headers=headers, json=body
    # )
    return r.json()


def get_in_progress(workspace):
    workspaceId = get_workspaceId(workspace)
    r = requests.get(
        f"{ENDPOINT}/workspaces/{workspaceId}/time-entries/in-progress", headers=headers
    )
    return r.json()


def finish_time_entry(workspace):
    current = get_in_progress(workspace)
    current_id = current["id"]
    body = {
        "start": current["timeInterval"]["start"],
        "billable": current["billable"],
        "description": current["description"],
        "projectId": current["projectId"],
        "taskId": current["taskId"],
        "tagIds": current["tagIds"],
        "end": get_current_time(),
    }
    r = requests.put(
        ENDPOINT + f"workspaces/{workspace}/timeEntries/{current_id}",
        headers=headers,
        json=body,
    )
    return r.json()


def get_time_entries(workspace=None):
    workspaceId = get_workspaceId(workspace)
    r = requests.get(
        f"{ENDPOINT}/workspaces/{workspaceId}/user/{CONFIG['uid']}/time-entries",
        headers=headers,
    )
    return r.json()[:10]


def get_workspaceId(workspace=None):
    if workspace:
        workspaceId = get_workspaces()[workspace]
    else:
        if CONFIG["wid"] != "":
            workspaceId = CONFIG["wid"]
        else:
            return set_workspace()[1]
    return workspaceId


def remove_time_entry(workspace, tid):
    r = requests.delete(
        ENDPOINT + f"workspaces/{workspace}/timeEntries/{tid}", headers=headers
    )
    return r.json()


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


def get_user():
    r = requests.get(f"{ENDPOINT}/user", headers=headers)
    return r.json()


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def cli(verbose):
    "Clockify terminal app"
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
        with open(config_file, "w") as f:
            json.dump(CONFIG, f)


@click.command("start", short_help="Start a new time entry")
@click.argument("workspace")
@click.argument("description")
@click.option(
    "--billable", is_flag=True, default=False, help="Set if entry is billable"
)
@click.option("--project", "-p", default=None, help="Project ID")
@click.option("--tag", "-g", multiple=True, help="Multiple tags permitted")
def start(workspace, description, billable, project, tag):
    ret = start_time_entry(workspace, description, billable, project, list(tag))
    if VERBOSE:
        print_json(ret)


@click.command("finish", short_help="Finish an on-going time entry")
@click.argument("workspace")
def finish(workspace):
    ret = finish_time_entry(workspace)
    if VERBOSE:
        print_json(ret)


@click.command("user", short_help="Get user information")
def user():
    user = get_user()
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


@click.command("set_workspace", short_help="Set the default work space")
@click.argument("workspace", type=str)
def s_workspace(workspace):
    name, wid = set_workspace(workspace)
    click.echo(f"Default workspace set to: {name}, {wid}")


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
                f"Start: {entry['timeInterval']['start']}, "
                + f"Duration: {re.sub('PT', '', entry['timeInterval']['duration'])}"
            )
            if info:
                mes += (
                    f", Description: {entry['description']}"
                    + f"End: {entry['timeInterval']['end']}, "
                    + f"ID: {entry['id']}"
                )
            click.echo(mes)


@click.command("entry", short_help="Remove entry")
@click.argument("-d", "--duration", type=str, default=None, help="Duration of entry in formats: h:m:s | h:m | h")
@click.option(
    "-w",
    "--workspace",
    "workspace",
    type=str,
    default=None,
    help="Default is set with set_workspace",
)
@click.option("--description", type=str, default=None, help="Entry description")
@click.option("-b", "--billable", is_flag=True, default=False, help="Set if entry is billable")
@click.option("--project", "-p", default=None, help="Project ID")
@click.option("--tag", "-t", multiple=True, help="Multiple tags permitted")
def add(workspace, description, billable, project, tag):
    ret = add_time_entry(workspace, duration, description, billable, project, list(tag))
    if VERBOSE:
        print_json(ret)


def remove_entry(workspace, tid):
    ret = remove_time_entry(workspace, tid)
    if VERBOSE:
        print_json(ret)


@click.command("remove_entry", short_help="Remove entry")
@click.argument("workspace")
@click.argument("time entry ID")
def remove_entry(workspace, tid):
    ret = remove_time_entry(workspace, tid)
    if VERBOSE:
        print_json(ret)

cli.add_command(start)
cli.add_command(finish)
cli.add_command(projects)
cli.add_command(workspaces)
cli.add_command(s_workspace)
cli.add_command(entries)
cli.add_command(remove_entry)
cli.add_command(user)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
