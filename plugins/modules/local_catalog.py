#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) Copyright IBM Corp. 2023
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: local_catalog
short_description: Create, remove, and manage the CICS local catalog
description:
  - Create, remove, and manage the L(local catalog,https://www.ibm.com/docs/en/cics-ts/latest?topic=catalogs-local-catalog)
    data set used by a CICS® region. CICS domains use the local catalog to save some of their information between CICS runs and 
    to preserve this information across a cold start.
  - You can use this module when provisioning or de-provisioning a CICS region, or when managing
    the state of the local catalog during upgrades or restarts.
  - Use the O(state) option to specify the intended state for the local
    catalog. For example, O(state=initial) will create and initialize a local
    catalog data set if it doesn't yet exist, or it will take an existing
    local catalog and empty it of all records.
author: Enam Khan (@enam-khan)
version_added: 1.1.0-beta.2
seealso:
  - module: global_catalog
options:
  space_primary:
    description:
      - The size of the primary space allocated to the local catalog data set.
        Note that this is just the value; the unit is specified with O(space_type).
      - This option takes effect only when the local catalog is being created.
        If the local catalog already exists, the option has no effect.
      - The size value of the secondary space allocation for the local catalog data set is 1; the unit is specified with O(space_type).
    type: int
    required: false
    default: 200
  space_type:
    description:
      - The unit portion of the local catalog data set size. Note that this is
        just the unit; the value is specified with O(space_primary).
      - This option takes effect only when the local catalog is being created.
        If the local catalog already exists, the option has no effect.
      - The size can be specified in megabytes (V(M)), kilobytes (V(K)),
        records (V(REC)), cylinders (V(CYL)), or tracks (V(TRK)).
    required: false
    type: str
    choices:
      - M
      - K
      - REC
      - CYL
      - TRK
    default: REC
  region_data_sets:
    description:
      - The location of the region data sets to be created using a template, for example, 
        C(REGIONS.ABCD0001.<< data_set_name >>).
      - If you want to use a data set that already exists, ensure that the data set is a local catalog data set.
    type: dict
    required: true
    suboptions:
      template:
        description:
          - The base location of the region data sets with a template.
        required: false
        type: str
      dfhlcd:
        description:
          - Overrides the templated location for the local catalog data set.
        required: false
        type: dict
        suboptions:
          dsn:
            description:
              - The data set name of the local catalog to override the template.
            type: str
            required: false
  cics_data_sets:
    description:
      - The name of the C(SDFHLOAD) library of the CICS installation, for example, C(CICSTS61.CICS.SDFHLOAD).
      - This module uses the C(DFHCCUTL) utility internally, which is found in the C(SDFHLOAD) library.
    type: dict
    required: true
    suboptions:
      template:
        description:
          - The templated location of the C(SDFHLOAD) library.
        required: false
        type: str
      sdfhload:
        description:
          - The location of the  C(SDFHLOAD) library to override the template.
        type: str
        required: false
  state:
    description:
      - The intended state for the local catalog, which the module will aim to
        achieve.
      - V(absent) will remove the local catalog data set entirely, if it
        already exists.
      - V(initial) will create the local catalog data set if it does not
        already exist, and empty it of all existing records.
      - V(warm) will retain an existing local catalog in its current state.
    choices:
      - "initial"
      - "absent"
      - "warm"
    required: true
    type: str
'''


EXAMPLES = r"""
- name: Initialize a local catalog
  ibm.ibm_zos_cics.local_catalog:
    region_data_sets:
      template: "REGIONS.ABCD0001.<< data_set_name >>"
    cics_data_sets:
      template: "CICSTS61.CICS.<< lib_name >>"
    state: "initial"

- name: Initialize a large catalog
  ibm.ibm_zos_cics.local_catalog:
    region_data_sets:
      template: "REGIONS.ABCD0001.<< data_set_name >>"
    cics_data_sets:
      template: "CICSTS61.CICS.<< lib_name >>"
    space_primary: 500
    space_type: "REC"
    state: "initial"

- name: Delete local catalog
  ibm.ibm_zos_cics.local_catalog:
    region_data_sets:
      template: "REGIONS.ABCD0001.<< data_set_name >>"
    cics_data_sets:
      template: "CICSTS61.CICS.<< lib_name >>"
    state: "absent"
"""


RETURN = r"""
changed:
  description: True if the state was changed, otherwise False.
  returned: always
  type: bool
failed:
  description: True if the query job failed, otherwise False.
  returned: always
  type: bool
start_state:
  description:
    - The state of the local catalog before the Ansible task runs.
  returned: always
  type: dict
  contains:
    vsam:
      description: True if the data set is a VSAM data set.
      returned: always
      type: bool
    exists:
      description: True if the local catalog data set exists.
      type: bool
      returned: always
end_state:
  description: The state of the local catalog at the end of the Ansible task.
  returned: always
  type: dict
  contains:
    vsam:
      description: True if the data set is a VSAM data set.
      returned: always
      type: bool
    exists:
      description: True if the local catalog data set exists.
      type: bool
      returned: always
executions:
  description: A list of program executions performed during the Ansible task.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: A human-readable name for the program execution.
      type: str
      returned: always
    rc:
      description: The return code for the program execution.
      type: int
      returned: always
    stdout:
      description: The standard out stream returned by the program execution.
      type: str
      returned: always
    stderr:
      description: The standard error stream returned from the program execution.
      type: str
      returned: always
"""


from ansible_collections.ibm.ibm_zos_core.plugins.module_utils.better_arg_parser import BetterArgParser
from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.dataset_utils import (
    _dataset_size, _data_set, _build_idcams_define_cmd)
from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.data_set import DataSet
from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.local_catalog import (
    _run_dfhccutl, _get_idcams_cmd_lcd)
from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.local_catalog import _local_catalog_constants as lc_constants
from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.data_set import _dataset_constants as ds_constants
from ansible_collections.ibm.ibm_zos_cics.plugins.module_utils.icetool import _run_icetool


class AnsibleLocalCatalogModule(DataSet):
    def __init__(self):
        super(AnsibleLocalCatalogModule, self).__init__()

    def init_argument_spec(self):  # type: () -> dict
        arg_spec = super(AnsibleLocalCatalogModule, self).init_argument_spec()

        arg_spec[ds_constants["PRIMARY_SPACE_VALUE_ALIAS"]].update({
            "default": lc_constants["PRIMARY_SPACE_VALUE_DEFAULT"]
        })
        arg_spec[ds_constants["PRIMARY_SPACE_UNIT_ALIAS"]].update({
            "default": lc_constants["SPACE_UNIT_DEFAULT"]
        })
        arg_spec[ds_constants["TARGET_STATE_ALIAS"]].update({
            "choices": lc_constants["TARGET_STATE_OPTIONS"]
        })
        arg_spec.update({
            ds_constants["REGION_DATA_SETS_ALIAS"]: {
                "type": "dict",
                "required": True,
                "options": {
                    "template": {
                        "type": "str",
                        "required": False,
                    },
                    "dfhlcd": {
                        "type": "dict",
                        "required": False,
                        "options": {
                            "dsn": {
                                "type": "str",
                                "required": False,
                            },
                        },
                    },
                },
            },
            ds_constants["CICS_DATA_SETS_ALIAS"]: {
                "type": "dict",
                "required": True,
                "options": {
                    "template": {
                        "type": "str",
                        "required": False,
                    },
                    "sdfhload": {
                        "type": "str",
                        "required": False,
                    },
                },
            },
        })
        return arg_spec

    def _get_arg_defs(self):  # type: () -> dict
        arg_def = super(AnsibleLocalCatalogModule, self)._get_arg_defs()

        arg_def[ds_constants["PRIMARY_SPACE_VALUE_ALIAS"]].update({
            "default": lc_constants["PRIMARY_SPACE_VALUE_DEFAULT"]
        })
        arg_def[ds_constants["PRIMARY_SPACE_UNIT_ALIAS"]].update({
            "default": lc_constants["SPACE_UNIT_DEFAULT"]
        })
        arg_def[ds_constants["TARGET_STATE_ALIAS"]].update({
            "choices": lc_constants["TARGET_STATE_OPTIONS"],
        })
        arg_def.update({
            ds_constants["REGION_DATA_SETS_ALIAS"]: {
                "arg_type": "dict",
                "required": True,
                "options": {
                    "template": {
                        "arg_type": "str",
                        "required": False,
                    },
                    "dfhlcd": {
                        "arg_type": "dict",
                        "required": False,
                        "options": {
                            "dsn": {
                                "arg_type": "data_set_base",
                                "required": False,
                            },
                        },
                    },
                },
            },
            ds_constants["CICS_DATA_SETS_ALIAS"]: {
                "arg_type": "dict",
                "required": True,
                "options": {
                    "template": {
                        "arg_type": "str",
                        "required": False,
                    },
                    "sdfhload": {
                        "arg_type": "data_set_base",
                        "required": False,
                    },
                },
            },
        })

        return arg_def

    def _get_data_set_object(self, size, result):  # type: (_dataset_size, dict) -> _data_set
        return _data_set(
            size=size,
            name=result.get(ds_constants["REGION_DATA_SETS_ALIAS"]).get("dfhlcd").get("dsn").upper(),
            sdfhload=result.get(ds_constants["CICS_DATA_SETS_ALIAS"]).get("sdfhload").upper(),
            state=result.get(ds_constants["TARGET_STATE_ALIAS"]),
            exists=False,
            vsam=False)

    def _get_data_set_size(self, result):  # type: (dict) -> _dataset_size
        return _dataset_size(
            unit=result.get(ds_constants["PRIMARY_SPACE_UNIT_ALIAS"]),
            primary=result.get(ds_constants["PRIMARY_SPACE_VALUE_ALIAS"]),
            secondary=lc_constants["SECONDARY_SPACE_VALUE_DEFAULT"])

    def validate_parameters(self):  # type: () -> None
        arg_defs = self._get_arg_defs()

        result = BetterArgParser(arg_defs).parse_args({
            ds_constants["REGION_DATA_SETS_ALIAS"]: self._module.params.get(ds_constants["REGION_DATA_SETS_ALIAS"]),
            ds_constants["CICS_DATA_SETS_ALIAS"]: self._module.params.get(ds_constants["CICS_DATA_SETS_ALIAS"]),
            ds_constants["PRIMARY_SPACE_VALUE_ALIAS"]: self._module.params.get(ds_constants["PRIMARY_SPACE_VALUE_ALIAS"]),
            ds_constants["PRIMARY_SPACE_UNIT_ALIAS"]: self._module.params.get(ds_constants["PRIMARY_SPACE_UNIT_ALIAS"]),
            ds_constants["TARGET_STATE_ALIAS"]: self._module.params.get(ds_constants["TARGET_STATE_ALIAS"])
        })

        size = self._get_data_set_size(result)
        self.data_set = self._get_data_set_object(size, result)

    def create_data_set(self):  # type: () -> None
        create_cmd = _build_idcams_define_cmd(_get_idcams_cmd_lcd(self.data_set))

        super().build_vsam_data_set(create_cmd, "Create local catalog data set")

    def delete_data_set(self):  # type: () -> None
        if not self.data_set["exists"]:
            self.result["end_state"] = {
                "exists": self.data_set["exists"],
                "vsam": self.data_set["vsam"]
            }
            self._exit()

        super().delete_data_set("Removing local catalog data set")

    def init_data_set(self):  # type: () -> None
        if self.data_set["exists"]:
            icetool_executions, record_count = _run_icetool(self.data_set["name"])
            self.result["executions"] = self.result["executions"] + icetool_executions
            if record_count["record_count"] > 0:
                # If records are present, empty the data set and rerun DFHCCUTL
                self.delete_data_set()
                self.data_set = self.get_data_set_state(self.data_set)
                self.create_data_set()

        else:
            self.create_data_set()

        try:
            ccutl_executions = _run_dfhccutl(self.data_set)
            self.result["executions"] = self.result["executions"] + ccutl_executions
        except Exception as e:
            self.result["executions"] = self.result["executions"] + e.args[1]
            self._fail(e.args[0])


def main():
    AnsibleLocalCatalogModule().main()


if __name__ == '__main__':
    main()
