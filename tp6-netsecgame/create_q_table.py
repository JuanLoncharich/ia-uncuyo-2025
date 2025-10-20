"""
create_q_table.py
===================

This script initialises an empty Q‑table for a high‑level Q‑learning agent
designed to operate in the NetSecGame environment.  The Q‑table maps from
abstract state identifiers to estimated Q‑values for the five high‑level
actions (scan network, find services, exploit service, find data and
exfiltrate data).  The resulting table and state mapping are stored in
``pickle`` format for later training.

Running the script will create a pickle file containing two items:

``q_table``
    A dictionary keyed by ``(state_id, action_name)`` with Q‑values (floats).

``state_mapping``
    A dictionary mapping internal state descriptors to unique integer
    identifiers.  When starting training you should load this file and
    continue updating both dictionaries.

Example usage:

.. code-block:: bash

   python3 create_q_table.py --output q_table_init.pkl

The default output path is ``q_table.pkl``.
"""

import argparse
import pickle


def main(filename: str) -> None:
    """Create an empty Q‑table and save it to ``filename``.

    Parameters
    ----------
    filename: str
        Path where the pickle file will be written.
    """
    data = {
        "q_table": {},
        "state_mapping": {},
    }
    with open(filename, "wb") as f:
        pickle.dump(data, f)
    print(f"Created empty Q‑table at {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialise an empty Q‑table for NetSecGame")
    parser.add_argument(
        "--output",
        help="Output filename for the pickle file",
        default="q_table.pkl",
        type=str,
    )
    args = parser.parse_args()
    main(args.output)