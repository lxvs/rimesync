from sys import stderr
from time import sleep
from pathlib import Path
from subprocess import run
from shutil import copyfile, copytree

__version__ = "0.1.0"

class RimeSync:
    def __init__(
            self,
            workspace: Path,
            rime_install_dir: Path,
            rime_user_dir: Path,
            rime_user_id: str,
            dry_run: bool = False,
    ) -> None:
        self.rime_install_dir = rime_install_dir
        self.rime_user_dir = rime_user_dir
        self.rime_sync_dir = rime_user_dir / 'sync' / rime_user_id if rime_user_id is not None else None
        self.dry_run = dry_run
        self.workspace = workspace
        print(self.workspace)

    def install(self, files: set[str], directories: set[str]):
        if not self.dry_run:
            print(f"install to: {self.rime_user_dir}")
            for f in files:
                src = self.workspace / 'rimedata' / f
                dst = self.rime_user_dir / f
                if not src.is_file():
                    continue
                print(src)
                try:
                    copyfile(src, dst)
                except Exception as e:
                    print(f"warning: failed to install {f}: {e}", file=stderr)
            for d in directories:
                src = self.workspace / 'rimedata' / d
                dst = self.rime_user_dir / d
                if not src.is_dir():
                    continue
                print(src)
                try:
                    copytree(src, dst)
                except Exception as e:
                    print(f"warning: failed to install {f}: {e}", file=stderr)
            print("call weasel deploy")
            run([self.rime_install_dir / 'WeaselDeployer.exe', '/deploy'], check=True)
            self.__wait(1)
        else:
            print(f"would install to: {self.rime_user_dir}")
            for f in files:
                src = self.workspace / 'rimedata' / f
                dst = self.rime_user_dir / f
                if not src.is_file():
                    continue
                print(src)
            for d in directories:
                src = self.workspace / 'rimedata' / d
                dst = self.rime_user_dir / d
                if not src.is_dir():
                    continue
                print(src)
            print("would call weasel deploy")
        print("install complete")

    def sync(self, files: set[str]):
        if not self.dry_run:
            print(f"sync with: {self.rime_sync_dir}")
            print("call weasel sync")
            run([self.rime_install_dir / 'WeaselDeployer.exe', '/sync'], check=True)
            self.__wait(1)

            print("merge userdb:")
            for f in files:
                src = self.workspace / 'rimedata' / f
                dst = self.rime_sync_dir / f
                if not src.is_file():
                    continue
                print(src)
                try:
                    copyfile(src, dst)
                    self.__wait(1)
                except Exception as e:
                    print(f"warning: failed to copy {f}: {e}", file=stderr)

            print("call weasel sync again")
            run([self.rime_install_dir / 'WeaselDeployer.exe', '/sync'], check=True)
            self.__wait(1)

            print("process and copy back userdb:")
            for f in files:
                src = self.rime_sync_dir / f
                dst = self.workspace / 'rimedata' / f
                if not src.is_file():
                    continue
                print(src)
                try:
                    with open(dst, 'wb') as g:
                        with open(src, 'rb') as h:
                            g.writelines(l for l in h if not l.startswith(b'\x7f'))
                except Exception as e:
                    print(f"warning: error in processing or writing {f}: {e}", file=stderr)
                    continue
        else:
            print(f"would sync with: {self.rime_sync_dir}")
            print("would call weasel sync")

            print("would merge userdb:")
            for f in files:
                src = self.workspace / 'rimedata' / f
                dst = self.rime_sync_dir / f
                if not src.is_file():
                    continue
                print(src)

            print("would call weasel sync agin")

            print("process and copy back userdb:")
            for f in files:
                src = self.rime_sync_dir / f
                dst = self.workspace / 'rimedata' / f
                if not src.is_file():
                    continue
                print(src)
        print("sync complete")

    @staticmethod
    def __wait(sec: int, prompt: str = "waiting"):
        print(f"{prompt} ", end='', flush=True)
        for t in f"{' '.join('.' * sec)}\n":
            sleep(0.5)
            print(t, end='', flush=True)
