#!/usr/bin/env python3

__package_name__ = "ptr-converter"
__version__ = "v0.1"
__license__ = "Unlicense"

__author__ = "mkow04"
__email__ = "maciejkowalski04@proton.me"

import sys
import ipaddress
from colorclasses import Color, Effect


def zone_deduper(zone: list) -> list:
    """
    Function deduplicating a zone, by asking the user which record to keep,
    and turning it into a list of [ip: hostname] entries
    """

    a_ips = [i[3] for i in zone]

    a_duped = {}
    a_deduped = []

    for i in zone:
        if a_ips.count(i[3]) > 1:
            a_duped.setdefault(i[3], [])
            a_duped[i[3]].append(i)
        else:
            a_deduped.append(i)

    for i in a_duped:
        print(f"\n{Color.BLUE}==> {Color.WHITE}Duplicated records found for IP {Color.GRAY}'{i}'{Color.WHITE}: {Effect.RESET}\n")
        for j in a_duped[i]:
            print(f"{a_duped[i].index(j)}: {j[0]}")
        input_index = int(input(f"\n{Color.GREEN}==> {Color.WHITE}Choose which one to keep: {Effect.RESET}"))
        a_deduped.append(a_duped[i][input_index])

    return [[i[3], i[0]] for i in a_deduped]


def make_ipv4_ptr(ipv4_list: list, domain: str, prefix: int = 24) -> list:
    """
    IPv4: Function making a PTR-like dictionary of tuples with entries like this: ("ptr zone", ("host", "fqdn"))
    """
    result = {}

    for ip, hostname in ipv4_list:
        octets = ip.split('.')

        if prefix >= 32:
            np = 3
        else:
            np = prefix//8

        hp = 4 - np

        zone = ".".join(octets[:np][::-1] + ["in-addr.arpa"])

        host = ".".join(octets[-hp:][::-1])

        fqdn = hostname + "." + domain + "."

        result.setdefault(zone, {})[host] = fqdn

    return result


def make_ipv6_ptr(ipv6_list: list, domain: str, prefix: int = 64) -> list:
    """
    IPv6: Function making a PTR-like dictionary of tuples with entries like this: ("ptr zone", ("host", "fqdn"))
    """
    result = {}

    for ip, hostname in ipv6_list:
        ipaddr: ipaddress.IPv6Address = ipaddress.ip_address(ip)
        ptr = ipaddr.reverse_pointer.split(".")

        if prefix >= 128:
            np = 32
        else:
            np = prefix//4

        hp = 32 - np

        zone = ".".join(ptr[np:34])

        host = ".".join(ptr[:hp])

        fqdn = hostname + "." + domain + "."

        result.setdefault(zone, {})[host] = fqdn

    return result


def main():
    """ Main """

    # Get zone from the user

    print(f"\n{Color.GREEN}==> {Color.WHITE}Provide A and AAAA records to be converted, press {Color.GRAY}'CTRL+D'{Color.WHITE} on a new line to submit: {Effect.RESET}\n")

    zones = sys.stdin.read()

    zone_list = zones.splitlines()

    # Filter zone

    zone_list = list(set(zone_list))  # Remove duplicates

    zone_list = [i for i in zone_list if i != ""]  # Remove empty lines

    zone_list = [i for i in zone_list if i[0] != ";"]  # Remove comments

    zone_list = [i.split() for i in zone_list]  # Split each line into a list

    # Separate A and AAAA records

    a_list = []
    aaaa_list = []

    for i in zone_list:
        if i[2] == "A":
            a_list.append(i)
        elif i[2] == "AAAA":
            aaaa_list.append(i)

    # Deduplicate

    a_list = zone_deduper(a_list)
    aaaa_list = zone_deduper(aaaa_list)

    # Get domain name

    domain = input(f"\n\n{Color.GREEN}==> {Color.WHITE}Provide a domain name for all the hosts in the provided zone: {Effect.RESET}\n")

    # Make PTR records

    a_pref = int(input(f"\n\n{Color.GREEN}==> {Color.WHITE}Provide a prefix lenght for IPv4 zones: {Effect.RESET}\n"))
    aaaa_pref = int(input(f"\n\n{Color.GREEN}==> {Color.WHITE}Provide a prefix lenght for IPv6 zones: {Effect.RESET}\n"))

    a_ptr_list = make_ipv4_ptr(a_list, domain, a_pref)
    aaaa_ptr_list = make_ipv6_ptr(aaaa_list, domain, aaaa_pref)

    # Give the result

    # IPv4

    print(f"\n\n{Color.YELLOW}==== {Color.WHITE}IPv4 Results:{Color.YELLOW} ===={Effect.RESET}\n")

    for k in a_ptr_list:
        v = a_ptr_list[k]
        print(f"\n{Effect.BOLD}{k}{Effect.RESET}")
        for vk in v:
            vv = v[vk]
            print(f"{vk}\tIN\tPTR\t{vv}")

    # IPv6

    print(f"\n\n{Color.YELLOW}==== {Color.WHITE}IPv6 Results:{Color.YELLOW} ===={Effect.RESET}\n")

    for k in aaaa_ptr_list:
        v = aaaa_ptr_list[k]
        print(f"\n{Effect.BOLD}{k}{Effect.RESET}")
        for vk in v:
            vv = v[vk]
            print(f"{vk}\tIN\tPTR\t{vv}")

    # Files for bind

    print(f"\n\n{Color.YELLOW}==== {Color.WHITE}Bind config:{Color.YELLOW} ===={Effect.RESET}\n")

    for k in a_ptr_list:
        print(f"zone {k} IN {"{"}")
        print("	type master;")
        print(f"	file \"/etc/bind/master/{k}\";")
        print("};")

    print()

    for k in aaaa_ptr_list:
        print(f"zone {k} IN {"{"}")
        print("	type master;")
        print(f"	file \"/etc/bind/master/{k}\";")
        print("};")

    print(f"\n\n{Color.YELLOW}==== {Color.WHITE}DONE{Color.YELLOW} ===={Effect.RESET}\n")


if __name__ == "__main__":
    line0 = f"{Color.CYAN}{Effect.BOLD}{__package_name__.upper()}  {Effect.RESET}{Effect.BOLD}{Effect.ITALIC}{__version__} {Effect.RESET}"
    line1 = f"{Color.CYAN}{Effect.BOLD}Author:{Effect.RESET} {__author__} {Effect.ITALIC}<{__email__}>{Effect.RESET}"

    lenght = 48

    print()

    print(f"{Color.DARK_CYAN}{'='*(lenght)}{Effect.RESET}")
    print(f" {line0}")
    print(f" {line1}")
    print(f"{Color.DARK_CYAN}{'='*(lenght)}{Effect.RESET}")

    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Color.RED}==> {Color.WHITE}Exitting, KeyboardInterrupt ...{Color.RED}{Effect.RESET}\n")
        exit(130)
    except EOFError:
        print(f"\n{Color.RED}==> {Color.WHITE}Exitting, EOFError ...{Color.RED}{Effect.RESET}\n")
        exit(0)
