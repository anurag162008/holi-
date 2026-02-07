from __future__ import annotations

from desktop_app.config import AppConfig
from desktop_app.ui import JarvisUI


def main() -> None:
    config = AppConfig()
    ui = JarvisUI(config)
    ui.run()


if __name__ == "__main__":
    main()
