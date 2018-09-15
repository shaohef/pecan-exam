import re, shutil, tempfile


#!define ADDR_INTERNAL "172.21.0.121"
# direction.edge="172.21.0.120" desc "Edge Server Local IP Address"
# $var(ret)=t_relay_to_udp("172.21.0.120","5060");
# $var(ret)=t_relay_to_tcp("172.21.0.120","5060");
#    $var(confsrvip)="172.21.0.119";
SIP_IP_RES = [(re.compile(r'(#!define ADDR_INTERNAL )"[\d.]{7,15}"'),
               r'\g<1>"%(sip)s"'),
               (re.compile(r'(direction.edge=)"[\d.]{7,15}"(.*)'),
               r'\g<1>"%(edge)s"\g<2>'),
               (re.compile(r'(\$var.*=t_relay_to_udp\()"[\d.]{7,15}",("\d{4,20}"\);)'),
               r'\g<1>"%(edge)s",\g<2>'),
               (re.compile(r'(\$var.*=t_relay_to_tcp\()"[\d.]{7,15}",("\d{4,20}"\);)'),
               r'\g<1>"%(edge)s",\g<2>'),
               (re.compile(r'(.*\$var\(confsrvip\)=)"[\d.]{7,15}";'),
               r'\g<1>"%(mcu)s";'),]

ips = {"sip": "111.111.111.113", "edge": "2.2.2.2", "mcu": "3.3.3.3"}


def sed_inplace(filename, patterns, **key):
    '''
    Perform the pure-Python equivalent of in-place `sed` substitution: e.g.,
    `sed -i -e 's/'${pattern}'/'${repl}' "${filename}"`.
    '''
    # For efficiency, precompile the passed regular expression.
    # pattern_compiled = re.compile(pattern)

    # For portability, NamedTemporaryFile() defaults to mode "w+b" (i.e., binary
    # writing with updating). This is usually a good thing. In this case,
    # however, binary writing imposes non-trivial encoding constraints trivially
    # resolved by switching to text writing. Let's do that.
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
        with open(filename) as src_file:
            for line in src_file:
                sub = line
                for res in patterns:
                    sub = res[0].sub(res[1] % key, sub)
                tmp_file.write(sub)

    # Overwrite the original file with the munged temporary file in a
    # manner preserving file attributes (e.g., permissions).
    shutil.copystat(filename, tmp_file.name)
    shutil.move(tmp_file.name, filename)

# Do it for Johnny.
# sed_inplace('/home/build/git/svc-iso/app/config/sip_config/kamailio'
#             '/kamailio.cfg', SIP_IP_RES, **ips)
