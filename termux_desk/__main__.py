"""Allow ``python -m termux_desk`` to work."""
from termux_desk.cli import main

raise SystemExit(main())
