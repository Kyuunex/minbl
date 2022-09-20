import ipaddress


def ip_decode(request):
    if request.headers.get("CF-Connecting-IP"):
        client_ip_address_str = request.headers.get("CF-Connecting-IP")
    else:
        client_ip_address_str = request.remote_addr

    if "." in client_ip_address_str:
        return 0, ipaddress.IPv4Address(client_ip_address_str)
    elif ":" in client_ip_address_str:
        return 1, ipaddress.IPv6Address(client_ip_address_str)
    else:
        raise ValueError("something is wrong")
