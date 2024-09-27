import os
from pathlib import Path
from dataclasses import dataclass
from argparse import ArgumentParser
import tomllib

from rimesync import RimeSync, __version__
from workspace import WORKSPACE

PROG = "rimesync"
MAIN_VERSION = "0"

@dataclass
class Config:
    rime_inst_dir: Path
    rime_user_dir: Path
    rime_user_id: str
    yamls: set[str]
    schemas: set[str]
    directories: set[str]
    include: set[str]
    exclude: set[str]

class RimeSyncConfigError(ValueError):
    pass

class RimeSyncMainError(RuntimeError):
    pass

def main():
    parser = parse_args()
    args = parser.parse_args()
    config = read_config(args.config)
    rs = RimeSync(
        WORKSPACE,
        config.rime_inst_dir,
        config.rime_user_dir,
        config.rime_user_id,
        args.dry_run,
    )

    if not args.install and not args.sync:
        parser.print_help()
        return

    if args.install:
        yaml_files = {f(x) for x in config.yamls for f in (lambda x: f'{x}.yaml', lambda x: f'{x}.custom.yaml')}
        schema_files = {f(x) for x in config.schemas for f in (lambda x: f'{x}.custom.yaml', lambda x: f'{x}.dict.yaml', lambda x: f'{x}.schema.yaml')}
        rs.install(yaml_files | schema_files | config.include - config.exclude, config.directories - config.exclude)

    if args.sync:
        rs.sync({f'{x}.userdb.txt' for x in config.schemas} - config.exclude)

def parse_args():
    parser = ArgumentParser(
        prog=PROG,
        allow_abbrev=False,
        epilog="use `%(prog)s <command> -h' for more info on specific command",
    )
    parser.add_argument(
        "-c",
        "--config",
        default='default.toml',
        help="path to the configuration file to use.  Default: %(default)s",
    )
    parser.add_argument(
        '-i',
        '--install',
        action='store_true',
        help="copy and deploy Rime data and configurations",
    )
    parser.add_argument(
        '-s',
        '--sync',
        action='store_true',
        help="sync userdb",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action='store_true',
        help="print what to do and exit",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"{__version__}.{MAIN_VERSION}",
    )

    return parser

def show_help() -> None:
    print("help")

def read_config(file) -> Config:
    with open(file, 'rb') as f:
        d = tomllib.load(f)

    if (rud := d.get('rime_user_dir')) is not None:
        rud = Path(os.path.expandvars(rud))
        if not (rud / 'installation.yaml').is_file():
            raise RimeSyncConfigError("invalid rime_user_dir: installation.yaml not found")
    elif (rud := guess_rime_user_dir()) is None:
        raise RimeSyncConfigError("no valid rime_user_dir found")

    if (rui := d.get('rime_user_id')) is None:
        with open(rud / 'installation.yaml', 'rt', encoding='utf-8') as f:
            for l in f:
                if l.startswith("installation_id: "):
                    rui = l.split(':')[1].strip(' "\n')

    if (rid := d.get('rime_install_dir')) is not None:
        rid = Path(os.path.expandvars(rid))
        if not (rid / 'WeaselDeployer.exe').is_file():
            raise RimeSyncConfigError("invalid rime_install_dir: WeaselDeployer.exe not found")
    else:
        v = None
        with open(rud / 'installation.yaml', 'rt', encoding='utf-8') as f:
            for l in f:
                if l.startswith("distribution_version: "):
                    v = l.split(':')[1].strip(' "\n')
        if v is None or (rid := guess_rime_inst_dir(v)) is None:
            raise RimeSyncConfigError("no valid rime_inst_dir found")

    return Config(
        rime_user_dir=rud,
        rime_user_id=rui,
        rime_inst_dir=rid,
        yamls=set(d.get('yamls', [])),
        schemas=set(d.get('schemas', [])),
        directories=set(d.get('directories', [])),
        include=set(d.get('include', [])),
        exclude=set(d.get('exclude', [])),
    )

def guess_rime_user_dir():
    if (appdata := os.environ.get("APPDATA")) is None:
        return None
    if not (p := Path(appdata, 'Rime')).is_dir():
        return None
    if not (p / 'installation.yaml').is_file():
        return None
    return p

def guess_rime_inst_dir(v):
    if (x := os.environ.get('ProgramFiles')) is not None and ((x := Path(x, 'Rime', f'weasel-{v}')) / 'WeaselDeployer.exe').is_file():
        return x
    if (x := os.environ.get('ProgramFiles(x86)')) is not None and ((x := Path(x, 'Rime', f'weasel-{v}')) / 'WeaselDeployer.exe').is_file():
        return x
    return None

if __name__ == '__main__':
    main()
