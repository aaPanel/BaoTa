#coding: utf-8
def extract_zone(domain_name):
    domain_name = domain_name.lstrip("*.")

    #处理地区域名
    top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn', 
                        '.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn', 
                        '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn', 
                        '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn']
    old_domain_name = domain_name
    m_count = domain_name.count(".")
    top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
    new_top_domain = "." + top_domain.replace(".","")
    is_tow_top = False
    if top_domain in top_domain_list:
        is_tow_top = True
        domain_name = domain_name[:-len(top_domain)] + new_top_domain #地区域名后缀去点处理

    if domain_name.count(".") > 1:
        zone, middle, last = domain_name.rsplit(".", 2)        
        acme_txt = "_acme-challenge.%s" % zone
        if is_tow_top: last = top_domain[1:] #还原地区域名
        root = ".".join([middle, last])
    else:
        zone = ""
        root = old_domain_name
        acme_txt = "_acme-challenge"
    return root, zone, acme_txt

def test(domain_name):
    domain_name = domain_name.lstrip("*.")
    subd = ""
    if domain_name.count(".") != 1:  # not top level domain
        pos = domain_name.rfind(".", 0, domain_name.rfind("."))
        subd = domain_name[:pos]
        domain_name = domain_name[pos + 1 :]
        if subd != "":
            subd = "." + subd
    return subd


#获取根域名
def get_root_domain(domain_name):
    if domain_name.count(".") != 1:  
        pos = domain_name.rfind(".", 0, domain_name.rfind("."))
        subd = domain_name[:pos]
        domain_name =  domain_name[pos + 1 :]
    return domain_name
    
#获取acmename
def get_acme_name(domain_name):
    d_root,tow_name,acme_txt = extract_zone(domain_name)
    return acme_txt + '.' + d_root

domain = "*.archenet.com.cn"
print(extract_zone(domain))
print(get_acme_name(domain))