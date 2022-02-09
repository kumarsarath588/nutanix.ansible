# This file is part of Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

from copy import deepcopy

from .prism import Prism
from .subnets import get_subnet_uuid


class Vpc(Prism):
    def __init__(self, module):
        resource_type = "/vpcs"
        super(Vpc, self).__init__(module, resource_type=resource_type)
        self.build_spec_methods = {
            "name": self._build_spec_name,
            "external_subnets": self._build_spec_external_subnet,
            "routable_ips": self._build_spec_routable_ips,
            "dns_servers": self._build_dns_servers,
        }

    def _get_default_spec(self):
        return deepcopy(
            {
                "api_version": "3.1.0",
                "metadata": {
                    "kind": "vpc",
                    "categories": {},
                },
                "spec": {
                    "name": None,
                    "resources": {
                        "common_domain_name_server_ip_list": [],
                        "external_subnet_list": [],
                        "externally_routable_prefix_list": [],
                    },
                },
            }
        )

    def _build_spec_name(self, payload, name):
        payload["spec"]["name"] = name
        return payload, None

    def _build_spec_external_subnet(self, payload, subnets):
        external_subnets = []
        for subnet in subnets:
            uuid, error = get_subnet_uuid(subnet, self.module)
            if error:
                return None, error
            subnet_ref_spec = self._get_external_subnet_ref_spec(uuid)
            external_subnets.append(subnet_ref_spec)

        payload["spec"]["external_subnet_list"] = external_subnets
        return payload, None

    def _build_spec_routable_ips(self, payload, ips):
        routable_ips = []
        for ip in ips:
            routable_ip_ref_spec = self._get_routable_ip_spec(
                ip["network_ip"], ip["network_prefix"]
            )
            routable_ips.append(routable_ip_ref_spec)

        payload["spec"]["externally_routable_prefix_list"] = routable_ips
        return payload, None

    def _build_dns_servers(self, payload, dns_servers):
        payload["spec"]["common_domain_name_server_ip_list"] = dns_servers
        return payload, None

    def _get_external_subnet_ref_spec(self, uuid):
        return deepcopy({"external_subnet_reference": {"kind": "subnet", "uuid": uuid}})

    def _get_routable_ip_spec(self, ip, prefix):
        return deepcopy({"ip": ip, "prefix_length": prefix})


##### Helper functions #####


def get_vpc_uuid(config, module):
    if "name" in config["vpc"]:
        vpc = Vpc(module)
        name = config["vpc"]["name"]
        uuid = vpc.get_uuid(name)
        if not uuid:
            error = "VPC {0} not found.".format(name)
            return None, error
    elif "uuid" in config["vpc"]:
        uuid = config["vpc"]["uuid"]
