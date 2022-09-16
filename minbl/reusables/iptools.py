import ipaddress


def ip_decode(client_ip_address_str):
    if "." in client_ip_address_str:
        return 0, ipaddress.IPv4Address(client_ip_address_str)
    elif ":" in client_ip_address_str:
        return 1, ipaddress.IPv6Address(client_ip_address_str)
    else:
        raise ValueError("something is wrong")
