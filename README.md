# nk2dl
Nuke to Deadline. A toolset for submitting nukescripts to Thinkbox Deadline in a "big studio" manner.

# pytest
    python -m pytest nk2dl/tests/ -v

# other tests

$env:PYTHONPATH = "C:/Users/Daniel/Documents/repo/nk2dl"
$env:DEADLINE_PATH = "C:/Program Files/Thinkbox/Deadline10/bin"
$env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
$env:NK2DL_DEADLINE_HOST = "192.168.1.18"
$env:NK2DL_DEADLINE_PORT = "4434"
$env:NK2DL_DEADLINE_SSL = "True"
$env:NK2DL_DEADLINE_SSL_CERT = "C:/Users/Daniel/Documents/repo/nk2dl/.ignore/webservice_certs/ca.crt"C:/Users/Daniel/Documents/repo/nk2dl/.ignore/webservice_certs/ca.crt"

python scripts/test_deadline_connection.py



$env:PYTHONPATH = "C:/Users/Daniel/Documents/repo/nk2dl"
$env:DEADLINE_PATH = "C:/Program Files/Thinkbox/Deadline10/bin"
$env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
$env:NK2DL_DEADLINE_HOST = "192.168.1.18"
$env:NK2DL_DEADLINE_PORT = "8081"
$env:NK2DL_DEADLINE_SSL = "False"

python scripts/test_deadline_connection.py
