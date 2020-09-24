# coding: utf-8
# The MIT License (MIT)
#
# Copyright (c) 2015 Daniel Roesler
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# Copyright Daniel Roesler, under MIT license, see LICENSE at github.com/diafygi/acme-tiny
import argparse, subprocess, json, os, sys, base64, binascii, time, hashlib, re, copy, textwrap, logging, requests

try:
    from urllib.request import urlopen, Request  # 3
except ImportError:
    from urllib2 import urlopen, Request  # 2

DEFAULT_CA = "https://acme-v02.api.letsencrypt.org"
# DEFAULT_CA = "https://acme-staging-v02.api.letsencrypt.org"
DEFAULT_DIRECTORY_URL = "https://acme-v02.api.letsencrypt.org/directory"  # 正式
# DEFAULT_DIRECTORY_URL = "https://acme-staging-v02.api.letsencrypt.org/directory "  # 测试

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.INFO)


def get_crt(account_key, csr, acme_dir, log=LOGGER, CA=DEFAULT_CA, disable_check=False, directory_url=DEFAULT_DIRECTORY_URL, contact=None):
    directory, acct_headers, alg, jwk = None, None, None, None  # global variables

    def _b64(b):
        return base64.urlsafe_b64encode(b).decode('utf8').replace("=", "")

    def _cmd(cmd_list, stdin=None, cmd_input=None, err_msg="Command Line Error"):
        proc = subprocess.Popen(cmd_list, stdin=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate(cmd_input)
        if proc.returncode != 0:
            raise IOError("{0}\n{1}".format(err_msg, err))
        return out

    def _do_request(url, data=None, err_msg="Error", depth=0):
        try:
            resp = urlopen(Request(url, data=data, headers={"Content-Type": "application/jose+json", "User-Agent": "acme-tiny"}))
            resp_data, code, headers = resp.read().decode("utf8"), resp.getcode(), resp.headers
        except IOError as e:
            resp_data = e.read().decode("utf8") if hasattr(e, "read") else str(e)
            code, headers = getattr(e, "code", None), {}
        try:
            resp_data = json.loads(resp_data)
        except ValueError:
            pass
        if depth < 100 and code == 400 and resp_data['type'] == "urn:ietf:params:acme:error:badNonce":
            raise IndexError(resp_data)
        if code not in [200, 201, 204]:
            # print("{0}:\nUrl: {1}\nData: {2}\nResponse Code: {3}".format(err_msg, url, data, code))
            sys.exit(json.dumps(resp_data))
        return resp_data, code, headers

    def _send_signed_request(url, payload, err_msg, depth=0):
        payload64 = _b64(json.dumps(payload).encode('utf8'))
        new_nonce = _do_request(directory['newNonce'])[2]['Replay-Nonce']
        protected = {"url": url, "alg": alg, "nonce": new_nonce}
        protected.update({"jwk": jwk} if acct_headers is None else {"kid": acct_headers['Location']})
        protected64 = _b64(json.dumps(protected).encode('utf8'))
        protected_input = "{0}.{1}".format(protected64, payload64).encode('utf8')
        out = _cmd(["openssl", "dgst", "-sha256", "-sign", account_key], stdin=subprocess.PIPE, cmd_input=protected_input, err_msg="OpenSSL Error")
        data = json.dumps({"protected": protected64, "payload": payload64, "signature": _b64(out)})
        try:
            return _do_request(url, data=data.encode('utf8'), err_msg=err_msg, depth=depth)
        except IndexError:  # retry bad nonces (they raise IndexError)
            return _send_signed_request(url, payload, err_msg, depth=(depth + 1))

    def _poll_until_not(url, pending_statuses, err_msg):
        while True:
            result, _, _ = _do_request(url, err_msg=err_msg)
            if result['status'] in pending_statuses:
                time.sleep(2)
                continue
            return result

    log.info("Parsing account key...")
    out = _cmd(["openssl", "rsa", "-in", account_key, "-noout", "-text"], err_msg="OpenSSL Error")
    pub_pattern = r"modulus:\n\s+00:([a-f0-9\:\s]+?)\npublicExponent: ([0-9]+)"
    pub_hex, pub_exp = re.search(pub_pattern, out.decode('utf8'), re.MULTILINE | re.DOTALL).groups()
    pub_exp = "{0:x}".format(int(pub_exp))
    pub_exp = "0{0}".format(pub_exp) if len(pub_exp) % 2 else pub_exp
    alg = "RS256"
    jwk = {
        "e": _b64(binascii.unhexlify(pub_exp.encode("utf-8"))),
        "kty": "RSA",
        "n": _b64(binascii.unhexlify(re.sub(r"(\s|:)", "", pub_hex).encode("utf-8"))),
    }
    accountkey_json = json.dumps(jwk, sort_keys=True, separators=(',', ':'))
    thumbprint = _b64(hashlib.sha256(accountkey_json.encode('utf8')).digest())

    # find domains
    log.info("Parsing CSR...")
    out = _cmd(["openssl", "req", "-in", csr, "-noout", "-text"], err_msg="Error loading {0}".format(csr))
    domains = set([])
    common_name = re.search(r"Subject:.*? CN\s?=\s?([^\s,;/]+)", out.decode('utf8'))
    if common_name is not None:
        domains.add(common_name.group(1))
    subject_alt_names = re.search(r"X509v3 Subject Alternative Name: \n +([^\n]+)\n", out.decode('utf8'), re.MULTILINE | re.DOTALL)
    if subject_alt_names is not None:
        for san in subject_alt_names.group(1).split(", "):
            if san.startswith("DNS:"):
                domains.add(san[4:])
    log.info("Found domains: {0}".format(", ".join(domains)))

    # get the ACME directory of urls
    log.info("Getting directory...")
    directory_url = CA + "/directory" if CA != DEFAULT_CA else directory_url  # backwards compatibility with deprecated CA kwarg
    directory, _, _ = _do_request(directory_url, err_msg="Error getting directory")
    log.info("Directory found!")

    # create account, update contact details (if any), and set the global key identifier
    log.info("Registering account...")
    reg_payload = {"termsOfServiceAgreed": True}
    account, code, acct_headers = _send_signed_request(directory['newAccount'], reg_payload, "Error registering")
    log.info("Registered!" if code == 201 else "Already registered!")
    if contact is not None:
        account, _, _ = _send_signed_request(acct_headers['Location'], {"contact": contact}, "Error updating contact details")
        log.info("Updated contact details:\n{0}".format("\n".join(account['contact'])))

    # create a new order
    log.info("Creating new order...")
    order_payload = {"identifiers": [{"type": "dns", "value": d} for d in domains]}
    order, _, order_headers = _send_signed_request(directory['newOrder'], order_payload, "Error creating new order")
    log.info("Order created!")

    # get the authorizations that need to be completed
    for auth_url in order['authorizations']:
        authorization, _, _ = _do_request(auth_url, err_msg="Error getting challenges")
        domain = authorization['identifier']['value']
        log.info("Verifying {0}...".format(domain))

        # find the http-01 challenge and write the challenge file
        challenge = [c for c in authorization['challenges'] if c['type'] == "http-01"][0]
        token = re.sub(r"[^A-Za-z0-9_\-]", "_", challenge['token'])
        keyauthorization = "{0}.{1}".format(token, thumbprint)
        wellknown_path = os.path.join(acme_dir, token)
        with open(wellknown_path, "w") as wellknown_file:
            wellknown_file.write(keyauthorization)

        # check that the file is in place
        # try:
        #     wellknown_url = "http://{0}/.well-known/acme-challenge/{1}".format(domain, token)
        #     assert (disable_check or _do_request(wellknown_url)[0] == keyauthorization)
        # except (AssertionError, ValueError) as e:
        #     os.remove(wellknown_path)
        #     raise ValueError("Wrote file to {0}, but couldn't download {1}: {2}".format(wellknown_path, wellknown_url, e))

        # say the challenge is done
        _send_signed_request(challenge['url'], {}, "Error submitting challenges: {0}".format(domain))
        authorization = _poll_until_not(auth_url, ["pending"], "Error checking challenge status for {0}".format(domain))
        if authorization['status'] != "valid":
            public.WriteFile(os.path.join(path, "check_authorization_status_response"), json.dumps(authorization), mode="w")
            print("Challenge did not pass for {0}".format(domain, ))
            sys.exit(json.dumps(authorization))
        log.info("{0} verified!".format(domain))

    # finalize the order with the csr
    log.info("Signing certificate...")
    csr_der = _cmd(["openssl", "req", "-in", csr, "-outform", "DER"], err_msg="DER Export Error")
    _send_signed_request(order['finalize'], {"csr": _b64(csr_der)}, "Error finalizing order")

    # poll the order to monitor when it's done
    order = _poll_until_not(order_headers['Location'], ["pending", "processing"], "Error checking order status")
    if order['status'] != "valid":
        raise ValueError("Order failed: {0}".format(order))

    # download the certificate
    certificate_pem, _, _ = _do_request(order['certificate'], err_msg="Certificate download failed")
    log.info("Certificate signed!")
    return certificate_pem


if __name__ == "__main__":  # 文件验证调用脚本

    os.chdir("/www/server/panel")
    if not 'class/' in sys.path:
        sys.path.insert(0,'class/')
    import public

    data = json.loads(sys.argv[1])
    print (data)
    sitedomain = data['siteName']
    path = data['path']
    public.ExecShell("mkdir -p {}".format(path))
    KEY_PREFIX = os.path.join(path, "privkey")
    ACCOUNT_KEY = os.path.join(path, "letsencrypt-account.key")
    DOMAIN_KEY = os.path.join(path, "privkey.pem")
    DOMAIN_DIR = data['sitePath']
    DOMAINS = data['DOMAINS']
    DOMAIN_PEM = KEY_PREFIX + ".pem"
    DOMAIN_CSR = KEY_PREFIX + ".csr"
    DOMAIN_CRT = KEY_PREFIX + ".crt"
    DOMAIN_CHAINED_CRT = os.path.join(path, "fullchain.pem")
    if not os.path.isfile(ACCOUNT_KEY):
        public.ExecShell('''openssl genrsa 4096 > "{}" '''.format(ACCOUNT_KEY))
        print ("Generate account key...")
    if not os.path.isfile(DOMAIN_KEY):
        public.ExecShell('''openssl genrsa 2048 > "{}" '''.format(DOMAIN_KEY))
        print ("Generate domain key...")
    OPENSSL_CONF = "/etc/ssl/openssl.cnf"
    if not os.path.isfile(OPENSSL_CONF):
        OPENSSL_CONF = "/etc/pki/tls/openssl.cnf"
        if not os.path.isfile(OPENSSL_CONF):
            sys.exit("错误，找不到文件openssl.cnf,请安装openssl")

    DOMAIN_CSR_shell = '''openssl req -new -sha256 -key "{}" -subj "/" -reqexts SAN -config <(cat {} <(printf "[SAN]\\nsubjectAltName=%s" "{}")) > "{}" '''.format(DOMAIN_KEY, OPENSSL_CONF, DOMAINS, DOMAIN_CSR)
    public.WriteFile(os.path.join(path, "DOMAIN_CSR_shell"), DOMAIN_CSR_shell, mode="w")
    result = public.ExecShell('''cd {} && chmod +x DOMAIN_CSR_shell && bash DOMAIN_CSR_shell'''.format(path, ))
    print ("Generate CSR...{}".format(DOMAIN_CSR))
    if result[1]:
        sys.exit(result[1])
    if os.path.isfile(DOMAIN_CRT):
        public.ExecShell('''mv "{}" "{}-OLD-$(date +%y%m%d-%H%M%S)" '''.format(DOMAIN_CRT, DOMAIN_CRT))

    DOMAIN_DIR = os.path.join(DOMAIN_DIR, ".well-known/acme-challenge/")
    public.ExecShell('''mkdir -p "{}" '''.format(DOMAIN_DIR))
    LOGGER.setLevel(LOGGER.level)
    signed_crt = get_crt(ACCOUNT_KEY, DOMAIN_CSR, DOMAIN_DIR, )  ##########
    public.WriteFile(DOMAIN_CRT, signed_crt, mode="w")
    signed_pem_path = os.path.join(path, "lets-encrypt-x3-cross-signed.pem")
    if not os.path.isfile(signed_pem_path):
        req = requests.get(url="https://letsencrypt.org/certs/lets-encrypt-x3-cross-signed.pem", verify=False)
        public.WriteFile(signed_pem_path, req.content, mode="w")
    public.ExecShell(''' cd {} && cat "{}" lets-encrypt-x3-cross-signed.pem > "{}" '''.format(path, DOMAIN_CRT, DOMAIN_CHAINED_CRT))
    print ("New cert: {} has been generated".format(DOMAIN_CHAINED_CRT))
    # time.sleep(5)
    # 重载Web服务配置
    if os.path.exists('/www/server/nginx/sbin/nginx'):
        result = public.ExecShell('/etc/init.d/nginx reload')
        if result[1].find('nginx.pid') != -1:
            public.ExecShell('pkill -9 nginx && sleep 1');
            public.ExecShell('/etc/init.d/nginx start');
    else:
        result = public.ExecShell('/etc/init.d/httpd reload')
