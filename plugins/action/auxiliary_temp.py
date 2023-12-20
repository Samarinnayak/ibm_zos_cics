# (c) Copyright IBM Corp. 2023
# Apache License, Version 2.0 (see https://opensource.org/licenses/Apache-2.0)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible_collections.ibm.ibm_zos_cics.plugins.controller_utils.module_action_plugin import (
    _ModuleActionPlugin,
)


class ActionModule(_ModuleActionPlugin):
    def run(self, tmp=None, task_vars=None):
        return super(ActionModule, self)._run(
            ds_name="dfhtemp",
            module_name="auxiliary_temp",
            cics_data_sets_required=False,
            tmp=tmp,
            task_vars=task_vars,
        )
