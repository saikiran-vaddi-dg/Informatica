"""
xml_parser.py
=============
Originally vendored from etl_mapping_compaction_api/stage2_xml_parser.py.

Deterministic, stdlib-only (xml.etree.ElementTree). Parses a raw PowerCenter
POWERMART export into the structured dataclasses from `common.py`, dropping
everything that isn't source, target, transformation, port, expression,
connector, mapping-variable, or session-partition-override semantics.

This is the ONE file that touches raw XML — every later stage works off the
structured objects this module returns.

Handles multi-mapping exports (a single file with more than one <MAPPING>
block) by returning one MappingInfo per mapping.
"""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from typing import Dict, List

from common import (
    ConnectorInfo,
    FieldDef,
    MappingInfo,
    MappingVariableInfo,
    MappletInfo,
    PartitionSqlOverride,
    PortInfo,
    SourceInfo,
    TargetInfo,
    TransformationInfo,
)


def _parse_fields(container: ET.Element, tag: str) -> List[FieldDef]:
    fields = []
    for el in container.findall(tag):
        fields.append(
            FieldDef(
                name=el.get("NAME", ""),
                datatype=el.get("DATATYPE", ""),
                precision=el.get("PRECISION", ""),
                scale=el.get("SCALE", ""),
            )
        )
    return fields


def _parse_transformation(el: ET.Element) -> TransformationInfo:
    ports = []
    for tf in el.findall("TRANSFORMFIELD"):
        ports.append(
            PortInfo(
                name=tf.get("NAME", ""),
                datatype=tf.get("DATATYPE", ""),
                precision=tf.get("PRECISION", ""),
                scale=tf.get("SCALE", ""),
                port_type=tf.get("PORTTYPE", ""),
                expression=tf.get("EXPRESSION") or None,
                group=tf.get("GROUP") or None,
                ref_field=tf.get("REF_FIELD") or None,
            )
        )
    table_attrs = {
        ta.get("NAME", ""): ta.get("VALUE", "")
        for ta in el.findall("TABLEATTRIBUTE")
        if ta.get("VALUE", "") != ""
    }
    groups = [
        {
            "name": g.get("NAME", ""),
            "type": g.get("TYPE", ""),
            "condition": g.get("EXPRESSION", ""),
            "description": g.get("DESCRIPTION", ""),
        }
        for g in el.findall("GROUP")
    ]
    return TransformationInfo(
        name=el.get("NAME", ""),
        type=el.get("TYPE", ""),
        reusable=el.get("REUSABLE", "NO") == "YES",
        description=el.get("DESCRIPTION", ""),
        ports=ports,
        table_attributes=table_attrs,
        groups=groups,
    )


def _parse_mapping_variables(mapping_el: ET.Element) -> List[MappingVariableInfo]:
    """<MAPPINGVARIABLE> children of <MAPPING> — `$$`-style parameters and
    variables. Not part of the port/connector graph, so nothing else in this
    module would otherwise surface them."""
    return [
        MappingVariableInfo(
            name=mv.get("NAME", ""),
            datatype=mv.get("DATATYPE", ""),
            default_value=mv.get("DEFAULTVALUE", ""),
            is_param=mv.get("ISPARAM", "NO") == "YES",
            is_expression_variable=mv.get("ISEXPRESSIONVARIABLE", "NO") == "YES",
            description=mv.get("DESCRIPTION", ""),
        )
        for mv in mapping_el.findall("MAPPINGVARIABLE")
    ]


def _parse_session_partition_overrides(folder: ET.Element, mapping_name: str) -> List[PartitionSqlOverride]:
    """Session transformation attribute overrides for this mapping.

    Most workflows store SQL/filter overrides under
    `SESSTRANSFORMATIONINST/PARTITION/ATTRIBUTE`, but some store them directly
    under `SESSTRANSFORMATIONINST/ATTRIBUTE`. Record both forms so summaries
    don't miss the effective runtime SQL."""
    overrides: List[PartitionSqlOverride] = []
    for session_el in folder.findall("SESSION"):
        if session_el.get("MAPPINGNAME", "") != mapping_name:
            continue
        session_name = session_el.get("NAME", "")
        for inst in session_el.findall("SESSTRANSFORMATIONINST"):
            instance_name = inst.get("SINSTANCENAME", "")
            transformation_type = inst.get("TRANSFORMATIONTYPE", "")
            for attr in inst.findall("ATTRIBUTE"):
                value = attr.get("VALUE", "")
                if not value:
                    continue
                overrides.append(
                    PartitionSqlOverride(
                        session_name=session_name,
                        instance_name=instance_name,
                        transformation_type=transformation_type,
                        partition_name=attr.get("PARTITIONNAME", ""),
                        attribute_name=attr.get("NAME", ""),
                        attribute_value=value,
                    )
                )
            for partition in inst.findall("PARTITION"):
                partition_name = partition.get("NAME", "")
                for attr in partition.findall("ATTRIBUTE"):
                    value = attr.get("VALUE", "")
                    if not value:
                        continue
                    overrides.append(
                        PartitionSqlOverride(
                            session_name=session_name,
                            instance_name=instance_name,
                            transformation_type=transformation_type,
                            partition_name=partition_name,
                            attribute_name=attr.get("NAME", ""),
                            attribute_value=value,
                        )
                    )
    return overrides


def parse_sources(folder: ET.Element) -> Dict[str, SourceInfo]:
    sources = {}
    for el in folder.findall("SOURCE"):
        name = el.get("NAME", "")
        sources[name] = SourceInfo(
            name=name,
            database_type=el.get("DATABASETYPE", ""),
            owner=el.get("OWNERNAME", ""),
            fields=_parse_fields(el, "SOURCEFIELD"),
        )
    return sources


def parse_targets(folder: ET.Element) -> Dict[str, TargetInfo]:
    targets = {}
    for el in folder.findall("TARGET"):
        name = el.get("NAME", "")
        targets[name] = TargetInfo(
            name=name,
            database_type=el.get("DATABASETYPE", ""),
            fields=_parse_fields(el, "TARGETFIELD"),
        )
    return targets


def parse_mapplets(folder: ET.Element) -> Dict[str, MappletInfo]:
    """Top-level reusable MAPPLET definitions (Stage 2c dedup source).

    Also captures a mapplet's own internal <CONNECTOR> wiring and its SOURCE
    instances' names — previously dropped — so a field_lineage trace that
    reaches into this mapplet can keep walking its actual port graph instead
    of stopping dead at the boundary with a generic placeholder."""
    mapplets = {}
    for el in folder.findall("MAPPLET"):
        name = el.get("NAME", "")
        inner_transformations = [_parse_transformation(t) for t in el.findall("TRANSFORMATION")]
        source_instances = [inst for inst in el.findall("INSTANCE") if inst.get("TYPE", "") == "SOURCE"]
        source_refs = [inst.get("TRANSFORMATION_NAME", inst.get("NAME", "")) for inst in source_instances]
        source_instance_names = [inst.get("NAME", "") for inst in source_instances]
        inner_connectors = [
            ConnectorInfo(
                from_field=c.get("FROMFIELD", ""),
                from_instance=c.get("FROMINSTANCE", ""),
                from_instance_type=c.get("FROMINSTANCETYPE", ""),
                to_field=c.get("TOFIELD", ""),
                to_instance=c.get("TOINSTANCE", ""),
                to_instance_type=c.get("TOINSTANCETYPE", ""),
            )
            for c in el.findall("CONNECTOR")
        ]
        mapplets[name] = MappletInfo(
            name=name,
            type="Mapplet",
            version=el.get("VERSIONNUMBER", ""),
            description=el.get("DESCRIPTION", ""),
            inner_transform_names=[t.name for t in inner_transformations],
            source_refs=source_refs,
            inner_transformations=inner_transformations,
            source_instance_names=source_instance_names,
            inner_connectors=inner_connectors,
        )
    return mapplets


def parse_mappings(folder: ET.Element, source_file: str, source_file_hash: str) -> List[MappingInfo]:
    """One MappingInfo per <MAPPING> element directly under FOLDER."""
    results = []
    for mapping_el in folder.findall("MAPPING"):
        name = mapping_el.get("NAME", "")

        transformations = [_parse_transformation(t) for t in mapping_el.findall("TRANSFORMATION")]

        instances = mapping_el.findall("INSTANCE")
        source_names, target_names, mapplet_refs = [], [], []
        instance_roles: Dict[str, str] = {}
        for inst in instances:
            itype = inst.get("TYPE", "")
            resolved_name = inst.get("TRANSFORMATION_NAME", inst.get("NAME", ""))
            instance_name = inst.get("NAME", resolved_name)
            role_type = inst.get("TRANSFORMATION_TYPE", itype).lower().replace(" ", "_")
            instance_roles[instance_name] = f"{role_type}:{resolved_name}"

            if itype == "SOURCE" and resolved_name not in source_names:
                source_names.append(resolved_name)
            elif itype == "TARGET" and resolved_name not in target_names:
                target_names.append(resolved_name)
            elif itype == "MAPPLET" and resolved_name not in mapplet_refs:
                mapplet_refs.append(resolved_name)

        connectors = [
            ConnectorInfo(
                from_field=c.get("FROMFIELD", ""),
                from_instance=c.get("FROMINSTANCE", ""),
                from_instance_type=c.get("FROMINSTANCETYPE", ""),
                to_field=c.get("TOFIELD", ""),
                to_instance=c.get("TOINSTANCE", ""),
                to_instance_type=c.get("TOINSTANCETYPE", ""),
            )
            for c in mapping_el.findall("CONNECTOR")
        ]

        all_sources = parse_sources(folder)
        all_targets = parse_targets(folder)

        results.append(
            MappingInfo(
                name=name,
                description=mapping_el.get("DESCRIPTION", ""),
                sources=[all_sources[n] for n in source_names if n in all_sources],
                targets=[all_targets[n] for n in target_names if n in all_targets],
                transformations=transformations,
                mapplet_refs=mapplet_refs,
                connectors=connectors,
                instance_roles=instance_roles,
                mapping_variables=_parse_mapping_variables(mapping_el),
                session_partition_overrides=_parse_session_partition_overrides(folder, name),
                source_file=source_file,
                source_file_hash=source_file_hash,
            )
        )
    return results


def parse_powercenter_export(path: str, file_hash: str = "") -> dict:
    """Top-level entry point for this stage.

    Returns
    -------
    {
      "sources": {name: SourceInfo},
      "targets": {name: TargetInfo},
      "mapplets": {name: MappletInfo},   # shared/reusable objects — feeds Stage 2c
      "mappings": [MappingInfo, ...],     # one per <MAPPING> block
    }
    """
    tree = ET.parse(path)
    root = tree.getroot()
    folder = root.find(".//FOLDER")
    if folder is None:
        raise ValueError(f"No <FOLDER> element found in {path} — not a PowerCenter export?")

    return {
        "sources": parse_sources(folder),
        "targets": parse_targets(folder),
        "mapplets": parse_mapplets(folder),
        "mappings": parse_mappings(folder, source_file=os.path.basename(path), source_file_hash=file_hash),
    }
