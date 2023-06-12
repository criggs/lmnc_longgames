import json, os
from pathlib import Path


class LongGameConfig:
    def __init__(self, file=None) -> None:
        file = (
            os.path.join(Path.home(), ".config/lmnc_longgames/config.json")
            if file is None
            else file
        )
        self.file = file
        self._config = None

    @property
    def config(self):
        if self._config is None:
            try:
                with open(self.file, "r") as openfile:
                    self._config = json.load(openfile)
            except FileNotFoundError:
                print("Initializing empty config")
                self._init_empty_config()
                self.write()
        return self._config

    def _init_empty_config(self):
        self._config = {
            "games": {"longpong": {}},
            "displays": {"main": {"devices": []}},
        }

    def write(self, output_file=None):
        output_file = self.file if output_file is None else output_file
        print(f"Writing to {output_file}")
        os.makedirs(os.path.dirname(self.file), exist_ok=True)
        with open(self.file, "w") as outfile:
            json.dump(self.config, outfile, indent=2)


def main():
    config = LongGameConfig()
    print(config.config)


if __name__ == "__main__":
    main()
