#! /usr/bin/env python3
"""OUI Lookup

This module provides functions to look up Organizationally Unique Identifiers (OUIs) for MAC addresses.
"""
import csv
import os

class OUILookup(object):
    def __init__(self):
        """
        OUI Lookup class
        """
        self._table = {}
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'resources', 'oui.csv')
        with open(file_path, newline='') as ouifile:
            ouireader = csv.reader(ouifile)
            for lines in ouireader:
                self._table[lines[1]] = lines[2]

    def match(self, mac: str) -> str | None:
        """
        Match a MAC address to its OUI entry.

        Parameters
        ----------
        mac : str
            The MAC address to match.

        Returns
        -------
        str | None
            The OUI entry if found, otherwise None.
        """
        tmp_mac = mac.replace(":", "").upper()
        found_mac = tmp_mac[:6]
        return self._table.get(found_mac)