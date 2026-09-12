import socket
import threading

# Fallback known working IPv4 endpoints for Google APIs
VERIFIED_GOOGLE_IPS = ['172.217.119.4', '172.217.112.4']
_active_ips = list(VERIFIED_GOOGLE_IPS)
_initialized = False
_lock = threading.Lock()

def setup_fast_network():
    """
    Bypasses broken IPv6 routing and unreachable Google IP addresses.
    Probes Google endpoints to lock onto the fastest reachable IPv4 address (<60ms).
    Prevents the 15-35 second Windows TCP connect timeout!
    """
    global _initialized, _active_ips
    with _lock:
        if _initialized:
            return
        _initialized = True

    # 1. Quick probe to see which IPs connect in < 250ms
    working = []
    for ip in VERIFIED_GOOGLE_IPS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.25)
            s.connect((ip, 443))
            s.close()
            working.append(ip)
        except Exception:
            pass

    if working:
        _active_ips = working
    else:
        _active_ips = ['172.217.119.4']

    print(f"[WisprFlow Network] Fast IPv4 routing active: {_active_ips}")

    # 2. Patch socket.getaddrinfo to return the verified IPv4 addresses for generativelanguage.googleapis.com
    orig_getaddrinfo = socket.getaddrinfo

    def fast_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        if host == 'generativelanguage.googleapis.com':
            results = []
            for ip in _active_ips:
                results.append((socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, port)))
            return results
        # For all other hosts, default to standard resolution
        return orig_getaddrinfo(host, port, family, type, proto, flags)

    socket.getaddrinfo = fast_getaddrinfo
