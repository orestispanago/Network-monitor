import xml.etree.ElementTree as ET
from models import Host


def get_xml_hosts(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    nmap_start = root.attrib.get("startstr")
    hosts = []
    for host in root.findall("host"):
        ip = mac = vendor = None
        for addr in host.findall("address"):
            if addr.attrib["addrtype"] == "ipv4":
                ip = addr.attrib["addr"]
            elif addr.attrib["addrtype"] == "mac":
                mac = addr.attrib["addr"]
                vendor = addr.attrib.get("vendor")
        host = Host(ip, mac, vendor, nmap_start)
        hosts.append(host)
    return hosts
