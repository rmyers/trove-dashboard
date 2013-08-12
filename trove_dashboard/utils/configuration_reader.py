from trove_dashboard.utils import horizon_attrs

__author__ = 'dmakogon'


def parse_logging_conf(logging_conf):
    parameters = {}
    try:
        with open(logging_conf, 'wb') as conf:
            for line in conf:
                if line != '\n':
                    k, v = line.split("=", 2)
                    parameters[k] = v.strip()
            return parameters
    except:
        raise IOError("File not found")
