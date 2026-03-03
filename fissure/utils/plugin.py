#!/usr/bin/python3
"""Plugin Related Functionality
"""
import asyncio
import csv
import filecmp
import importlib.util
import inspect
import logging
import os
from psycopg2.extensions import connection
import shutil
from subprocess import Popen, run
import traceback
from typing import List

from fissure.utils import FISSURE_ROOT, PLUGIN_DIR
from fissure.utils.library import (
    openDatabaseConnection,
    addProtocol,
    removeProtocol,
    addModulationType,
    removeModulationType,
    addPacketType,
    removePacketType,
    addSOI,
    removeSOI,
    addDemodulationFlowGraph,
    removeDemodulationFlowGraph,
    addAttack,
    removeAttack,
)


TABLES_FUNCTIONS = [
    ('attacks.csv', addAttack, removeAttack),
    ('demodulation_flow_graphs.csv', addDemodulationFlowGraph, removeDemodulationFlowGraph),
    ('modulation_types.csv', addModulationType, removeModulationType),
    ('packet_types.csv', addPacketType, removePacketType),
    ('protocols.csv', addProtocol, removeProtocol),
    ('soi_data.csv', addSOI, removeSOI)
]

async def get_fissure_plugin_editor_plugins_path() -> str:
    """Get the path to the FISSURE Plugin Editor plugins directory.

    Returns
    -------
    str
        Path to the FISSURE Plugin Editor plugins directory.
    """
    if shutil.which("fissure-plugin-editor") is not None:
        proc = await asyncio.create_subprocess_exec(
            "fissure-plugin-editor", "plugins", "-d",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode().strip()
        if output.startswith("Plugins directory:"):
            return output.split("Plugins directory:")[1].strip()
        else:
            return None
    else:
        return None

def launch_fissure_plugin_editor() -> bool:
    """Launch the FISSURE Plugin Editor.

    Returns
    -------
    bool
        True if the editor was launched successfully, False otherwise.
    """
    try:
        # Launch the FISSURE Plugin Editor in a new terminal
        Popen(["fissure-plugin-editor", "gui"])
    except FileNotFoundError:
        return False

    # Check if the process is running
    result = run(["pgrep", "-f", "fissure-plugin-editor"], capture_output=True)
    return bool(result.stdout.strip())

def get_local_plugin_names():
    """
    
    """
    # Scan plugins file directory; get plugin names based on plugin folder/compressed
    plugins = []
    for candidate in os.listdir(PLUGIN_DIR):
        candidate_path = os.path.join(PLUGIN_DIR, candidate)
        if os.path.isdir(candidate_path):
            # plugin folder
            plugins += [candidate]
        elif os.path.isfile(candidate_path):
            (root, ext) = os.path.splitext(candidate)
            if ext == '.zip':
                # plugin zip file; use root name
                plugins += [root]
    return plugins

def get_plugin_actions(plugin: str, logger: logging.getLogger = logging.getLogger(__name__)) -> List[str]:
    """Get Plugin Actions

    Parameters
    ----------
    plugin : str
        Plugin name

    Returns
    -------
    List[str]
        List of action names
    """
    actions_path = os.path.join(PLUGIN_DIR, plugin, 'actions.py')
    actions = []
    if os.path.exists(actions_path):
        try:
            spec = importlib.util.spec_from_file_location("actions", actions_path)
            if spec is None or spec.loader is None:
                # Could not create a valid spec/loader for the actions module
                raise ImportError(f"Cannot load module spec for {actions_path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            actions = [name for name, obj in inspect.getmembers(module, inspect.isfunction) if not name.startswith('_')]  # Exclude private functions
        except Exception as e:
            logger.error(f"Failed to load actions from {actions_path}: {e}")
            logger.debug("Traceback while loading actions:\n%s", traceback.format_exc())
    return actions

def apply_csv_to_table(conn:connection, file: str, function: object):
    """Apply CSV Rows to PostgreSQL Table

    Parameters
    ----------
    conn : connection
        Database connection
    file : str
        CSV file
    function : object
        Function to apply changes
    """
    with open(file, 'r') as f:
        reader = csv.reader(f,dialect='unix',quotechar="'")
        for row in reader:
            _ = function(conn, *row[1:])


def modify_database(logger: logging.getLogger=logging.getLogger(__name__), plugin_names:List[str] = None, action:str='add'):
    """Modify PostgreSQL Database

    Modify tables in the PostgreSQL database using rows in CSV files. Expected tables are in `fissure.utils.plugins.TABLES_FUNCTIONS`.

    Parameters
    ----------
    conn : connection
        Database connection
    paths : str
        Path(s) to csv files
    action : str, optional
        Action to apply from set {'add', 'remove'}, by default 'add'

    Raises
    ------
    RuntimeError
        _description_
    """
    # Parse Action
    if action.lower() == 'add':
        fcn_idx = 1
    elif action.lower() == 'remove':
        fcn_idx = 2
    else:
        logger.error('`action` must be in set {"add", "remove"}')

    for plugin_name in plugin_names:
        # Apply Changes to Database
        conn = openDatabaseConnection()
        try:
            for functions in TABLES_FUNCTIONS:
                apply_csv_to_table(conn, os.path.join(PLUGIN_DIR, plugin_name, 'tables/', functions[0]), functions[fcn_idx])
        except:
            logger.error('Failure to apply action "' + str(action) + '" to the database for plugin ' + str(plugin_name))
        finally:
            conn.close()


def install(plugin: str):
    """Install Plugin

    Copies files from the `PLUGIN_DIR`/`plugin`/install_files directory into the main FISSURE file structure.

    Parameters
    ----------
    plugin : str
        Plugin name
    """
    # Copy flow graph library files into directory
    # Get install files directory path
    install_files = os.path.join(PLUGIN_DIR, plugin, 'install_files')

    # Copy Files to FISSURE Directories
    shutil.copytree(install_files, FISSURE_ROOT, symlinks=True, dirs_exist_ok=True)


def installed(plugin: str) -> bool:
    """Check if Plugin is Installed

    Parameters
    ----------
    plugin : str
        Plugin name

    Returns
    -------
    bool
        True if files within FISSURE match plugin files, False otherwise
    """
    if os.path.exists(os.path.join(PLUGIN_DIR, plugin)):
        return _installed(os.path.join(PLUGIN_DIR, plugin, 'install_files'), FISSURE_ROOT)
    else:
        return False


def _installed(path1: os.PathLike, path2: os.PathLike) -> bool:
    """Recursive Installed File Check

    Intended to be used with `installed`. `path1` is the baseline for files expected to be in `path2` to meet installed criteria.

    Parameters
    ----------
    path1 : os.PathLike
        Baseline path
    path2 : os.PathLike
        Target path

    Returns
    -------
    bool
        True if files and file structure of `path1` are within `path2`, False otherwise
    """
    path1_list = os.listdir(path1)
    path2_list = os.listdir(path2)
    for item in path1_list:
        path1_path = os.path.join(path1, item)
        path2_path = os.path.join(path2, item)
        if not item in path2_list:
            # Item Path not in path2
            return False
        elif os.path.isdir(path1_path):
            # Item is a Directory
            if not os.path.isdir(path2_path):
                # Item is not a Directory in path2
                return False
            elif not _installed(path1_path, path2_path):
                # Recursive Search Found Differences
                return False
        else:
            # path1 Item is a File
            if not filecmp.cmp(path1_path, path2_path):
                # Files Fail Comparison
                return False

    return True


def uninstall(plugin: str):
    """Uninstall Plugin

    Removes files in the main FISSURE file structure that are identified based on files in the `plugin_path`/install_files directory.

    **WARNING:** No name mangling is used. If a file is the same as one in FISSURE or another plugin it will be removed.

    Parameters
    ----------
    plugin : str
        Plugin name
    """
    plugin_path = os.path.join(PLUGIN_DIR, plugin, 'install_files')
    if os.path.exists(plugin_path):
        _uninstall(plugin_path, FISSURE_ROOT)


def _uninstall(path1: os.PathLike, path2: os.PathLike):
    """Recursive Uninstall Plugin Function

    Intended to be used with `uninstall`. `path1` is the baseline for files expected to be uninstalled from `path2`.

    Parameters
    ----------
    path1 : os.PathLike
        Baseline path
    path2 : os.PathLike
        Target path
    """
    path1_list = os.listdir(path1)
    for item in path1_list:
        path1_path = os.path.join(path1, item)
        path2_path = os.path.join(path2, item)
        if os.path.isdir(path1_path) and os.path.isdir(path2_path):
            if _uninstall(path1_path, path2_path):
                os.rmdir(path2_path)
        elif os.path.exists(path2_path):
            if filecmp.cmp(path1_path, path2_path):
                os.remove(path2_path)
    return len(os.listdir(path2)) == 0 # indicate if directory is empty


def remove(plugin: str):
    """Remove Plugin from File System

    **WARNING:** No name mangling is used. If a file is the same as one in FISSURE or another plugin it will be removed.

    Parameters
    ----------
    plugin : str
        Plugin name
    """
    plugin_path = os.path.join(PLUGIN_DIR, plugin)
    if os.path.exists(plugin_path):
        uninstall(plugin)
        shutil.rmtree(os.path.join(PLUGIN_DIR, plugin))


def install_to_database(plugin: str):
    """Plugin to install to the database

    Parameters
    ----------
    plugin : str
        Plugin name
    """
    plugin_path = os.path.join(PLUGIN_DIR, plugin)
    run(['python', os.path.join(plugin_path, 'installer.py'), '-i'])


def remove_from_database(plugin: str):
    """Plugin to remove from the database

    Parameters
    ----------
    plugin : str
        Plugin name
    """
    plugin_path = os.path.join(PLUGIN_DIR, plugin)
    run(['python', os.path.join(plugin_path, 'installer.py'), '-u'])


def get_action_schema(plugin: str, action_name: str,
                      logger: logging.getLogger = logging.getLogger(__name__)) -> dict:
    """
    Get Action Schema

    Looks for a variable named:  <action_name>_schema  inside the plugin's actions.py
    Example: promote_to_soi_schema = {"params": [...]}

    Returns {"params": []} if not found or on failure.
    """
    actions_path = os.path.join(PLUGIN_DIR, plugin, "actions.py")

    if not os.path.exists(actions_path):
        return {"params": []}

    try:
        # Use a unique module name to reduce collisions if multiple plugins are loaded
        spec = importlib.util.spec_from_file_location(f"{plugin}_actions", actions_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module spec for {actions_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        schema_attr = f"{action_name}_schema"
        schema = getattr(module, schema_attr, None)

        if isinstance(schema, dict):
            # Minimal sanity check: must have params list if present
            params = schema.get("params", [])
            if isinstance(params, list):
                return schema

        return {"params": []}

    except Exception as e:
        logger.error(f"Failed to load action schema from {actions_path}: {e}")
        logger.debug("Traceback while loading schema:\n%s", traceback.format_exc())
        return {"params": []}