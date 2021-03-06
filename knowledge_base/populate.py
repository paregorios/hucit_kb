#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Matteo Romanello, matteo.romanello@gmail.com

import ipdb as pdb
import os
import json
import logging
from MyCapytain.resolvers.cts.api import HttpCtsResolver
from MyCapytain.retrievers.cts5 import HttpCtsRetriever

logger = logger = logging.getLogger(__name__)

"""
NB: needs to run under Py3

Notes on fetching less common/stable text structures (Bekker, Stephanus).

**Problem**: the Leipzig CTS API exposes only Stephanus pages (e.g. 17)
            but not Stephanus sections (e.g. 17a). but the sections are there
            in the TEI XML, marked up as `tei"milestone` elements.

**Solution**: a solution to this is to fetch the first level via the API,
            and extract the second level units directly from the TEI/XML
            via xpath.

`resolver.getPassage()\
.export(output=Mimetypes.PYTHON.ETREE).xpath(".//tei:milestone")` ecc

"""


def fetch_text_structure(urn, endpoint="http://cts.perseids.org/api/cts"):
    """
    Fetches the text structure of a given work from a CTS endpoint.

    :param urn: the work's CTS URN (at the work-level!,
        e.g."urn:cts:greekLit:tlg0012.tlg001")
    :type urn: string
    :param endpoint: the URL of the CTS endpoint to use (defaults to Perseids')
    :type endpoint: string
    :return: a dict with keys "urn", "provenance", "valid_reffs", "levels"
    :rtype: dict
    """

    structure = {
        "urn": urn,
        "provenance": endpoint,
        "valid_reffs": {}
    }

    orig_edition = None
    suffix = 'grc' if 'greekLit' in urn else 'lat'
    resolver = HttpCtsResolver(HttpCtsRetriever(endpoint))
    work_metadata = resolver.getMetadata(urn)

    # among all editions for this work, pick the one in Greek or Latin
    try:
        orig_edition = next(iter(
            work_metadata.children[edition]
            for edition in work_metadata.children
            if suffix in str(work_metadata.children[edition].urn)
        ))
    except Exception as e:
        print(e)
        return None

    assert orig_edition is not None

    # get information about the work's citation scheme
    structure["levels"] = [
        (n + 1, level.name.lower())
        for n, level in enumerate(orig_edition.citation)
    ]

    # for each hierarchical level of the text
    # fetch all citable text elements
    for level_n, level_label in structure["levels"]:

        structure["valid_reffs"][level_n] = []
        for ref in resolver.getReffs(urn, level=level_n):
            print(ref)
            element = {
                "current": "{}:{}".format(urn, ref),
            }
            if "." in ref:
                element["parent"] = "{}:{}".format(
                    urn,
                    ".".join(ref.split(".")[:level_n - 1])
                )
            textual_node = resolver.getTextualNode(
                textId=urn,
                subreference=ref,
                prevnext=True
            )
            if textual_node.nextId is not None:
                element["previous"] = "{}:{}".format(urn, textual_node.nextId)
            if textual_node.prevId is not None:
                element["following"] = "{}:{}".format(urn, textual_node.prevId)
            structure["valid_reffs"][level_n].append(element)

    return structure


def download_text_structure(urn, basedir):
    """

    Example:

    >>> download_text_structure(
        'urn:cts:greekLit:tlg0012.tlg001',
        '/Users/rromanello/Documents/ClassicsCitations/hucit_kb/knowledge_base/data/text_structures'
    )
    """

    text_structure = fetch_text_structure(urn)
    path = os.path.join(basedir, "{}.json".format(urn.replace(":", "-")))
    with open(path, 'w') as ofile:
        json.dump(text_structure, ofile)


def populate_text_structure(urn, ts):  # TODO: implement
    """
    TODO

    Logic:
    * check whether the work already has a TextStructure
    * otherwise add a new one
    * ts.add_levels([level[1] for level in ts["levels"]])
    * for each level, add the TextElements
    """
    return
