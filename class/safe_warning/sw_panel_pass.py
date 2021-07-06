#!/usr/bin/python
#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# 是否修改面板默认帐号密码
# -------------------------------------------------------------------

import os,sys,re,public

_title = '面板密码是否安全'
_version = 1.0                              # 版本
_ps = "检测面板帐号密码是否安全"              # 描述
_level = 0                                  # 风险级别： 1.提示(低)  2.警告(中)  3.危险(高)
_date = '2020-08-04'                        # 最后更新时间
_ignore = os.path.exists("data/warning/ignore/sw_panel_pass.pl")
_tips = [
    "请到【设置】页面修改面板帐号密码",
    "注意：请不要使用过于简单的帐号密码，以免造成安全隐患",
    "推荐使用高安全强度的密码：分别包含数字、大小写、特殊字符混合，且长度不少于7位。",
    ]
_help = ''

def check_run():
    '''
        @name 开始检测
        @author hwliang<2020-08-04>
        @return tuple (status<bool>,msg<string>)
    '''

    default_file = '/www/server/panel/default.pl'
    if not os.path.exists(default_file):
        return True,'无风险'
    default_pass = public.readFile(default_file).strip()
    
    p1 = password_salt(public.md5(default_pass),uid=1)
    find = public.M('users').where('id=?',(1,)).field('username,password').find()
    if p1 == find['password']:
        return False,'未修改面板默认密码，存在安全隐患'

    lower_pass_txt = '''12123
china
test
test12
test11
test1
test2
test123
bt.cn
www.bt.cn
admin
root
12345
123456
123456789
111111
from91
12345678
123123
5201314
000000
11111111
a123456
163.com
fill.com
123321
123123123
00000000
1314520
7758521
1234567
666666
123456a
1234567890
woaini
a123456789
888888
88888888
147258369
qq123456
654321
zxcvbnm
woaini1314
112233
5211314
123456abc
520520
aaaaaa
123654
987654321
123456789a
12345
7758258
100200
147258
111222
abc123456
111222tianya
121212
1111111
abc123
110110
admin123
789456
q123456
123456aa
aa123456
asdasd
999999
123qwe
789456123
1111111111
1314521
iloveyou
qwerty
password
qazwsx
159357
222222
woaini520
woaini123
521521
asd123
qqqqqq
qq1111
1234
qwe123
111111111
1qaz2wsx
qwertyuiop
5201314520
asd123456
159753
31415926
qweqwe
555555
333333
woaini521
abcd1234
ASDFGHJKL
123456qq
11223344
456123
123000
123698745
wangyut2
201314
zxcvbnm123
qazwsxedc
1q2w3e4r
z123456
123abc
a123123
12345678910
asdfgh
456789
qwe123456
321321
123654789
456852
0000000000
WOAIWOJIA
741852963
5845201314
aini1314
0123456789
a321654
123456123
584520
778899
520520520
7777777
q123456789
123789
zzzzzz
qweasdzxc
5845211314
123456q
w123456
12301230
qq123456789
wocaonima
qq123123
a5201314
a12345678
asdasdasd
a1234567
147852
110120
135792468
CAONIMA
963852741
3.1415926
1234560
101010
7758520
753951
666888
zxc123
0000000
zhang123
987654
a111111
1233211234567
789789
25257758
7708801314520
zzzxxx
1111
999999999
1357924680
yahoo.com.cn
123456789q
12341234
5841314520
zxc123456
yangyang
168168
123123qaz
abcd123456
456456
963852
as123456
741852
xiaoxiao
1230123
555666
000000000
369369
211314
102030
aaa123456
zxcvbn
110110110
buzhidao
qaz123
123456.
asdfasdf
123456789.
woainima
123456ASD
woshishui
131421
123321123
dearbook
1234qwer
qaz123456
aaaaaaaa
111222333
qq5201314
3344520
147852369
1q2w3e
windows
123456987
zz12369
qweasd
qiulaobai
66666666
12344321
qwer1234
a12345
7894561230
qwqwqw
777777
110120119
951753
wmsxie123
131420
1314520520
369258147
321321321
110119
beijing2008
321654
a000000
147896325
12121212
123456aaa
521521521
22222222
888999
123456789ABC
abc123456789
12345678900
1q2w3e4r5t
1234554321
www123456
w123456789
336699
abcdefg
709394
258369
z123456789
314159
584521
12345678a
7788521
9876543210
258258
111111a
87654321
123asd
5201314a
134679
135246
hotmail.com
123123a
11112222
131313
100200300
11111
1234567899
520530
251314
qq66666
yahoo.cn
123456qwe
worinima
sohu.com
NULL
518518
123457
q1w2e3r4
721521
123456789QQ
584131421
qw123456
123456..
0123456
135790
3344521
980099
a1314520
123456123456
qazwsx123
asdf1234
444444
123456z
120120
wang123456
12345600
7758521521
12369874
abcd123
a12369
li123456
1234567891
wang123
1234abcd
147369
zhangwei
qqqqqqqq
521125
010203
369258
654123
woailaopo
QAZQAZ
121314
1qazxsw2
zxczxc
l123456
111000
jingjing
0000
1472583690
25251325
langzi123
wojiushiwo
7895123
wangjian
123qweasd
110120130
1123581321
142536
584131420
aaa123
aaa111
woaiwoziji
520123
665544
ab123456
a123456a
fuckyou
99999999
5203344
qwertyui
521314
18881888
584201314
woaini@
7654321
20082008
520131
124578
852456
nihaoma
74108520
232323
55555555
zx123456
wwwwww
119119
weiwei
13145200
LOVE1314
564335
123456789123
wo123456
123520
52013145201314
loveyou
wolf8637
112358
5201314123
yuanyuan
zhanglei
zz123456
1234567A
a11111
000000a
321654987
xiaolong
5841314521
shmily
520025
159951
77585210
tiantian
134679852
QWASZX
123456654321
20080808
zhangjian
123465
9958123
159159
5508386
wangwei
5205201314
woaini5201314
888666
52013141314
qweqweqwe
1122334455
123456789z
585858
33333333
aa123123
qwertyuiop123
q111111
9638527410
911911
qqq111
5213344
sunshine
liu123456
abcdef
zhendeaini
007007
555888
qq111111
jiushiaini
mnbvcxz
xiaoqiang
445566
nicholas
dongdong
123456abcd
111qqq
aptx4869
258456
wobuzhidao
qazxsw
123789456
zhang123456
7215217758991
1234567890123
......
huang123
maomao
222333
wangyang
123456789aa
1.23457E+11
1234566
1230456
1a2b3c4d
13141314
a7758521
123456zxc
123456as
forever
s123456
12348765
xxxxxx
asdf123
a1b2c3d4
246810
333666
mingming
000123
jiajia
12qwaszx
ffffff
112233445566
77585211314
520131400
aa123456789
wpc000821
WANGJING
woaini1314520
&nbsp
000111
qq1314520
1234512345
147147
123456qaz
q123123
123456ab
xiaofeng
wodemima
shanshan
w2w2w2
666999
123456w
321456
feifei
dragon
computer
dddddd
zhangjie
baobao
x123456
q1w2e3
chenchen
12345679
131452
caonima123
asdf123456
tangkai
52013140
longlong
ssssss
www123
1234568
q1q1q1q1
asdfghjkl123
14789632
123456711
michael
tingting
woshishei
asd123456789
1314258
sunliu66
qwert12345
235689
565656
1234569
ww123456
1314159
5211314521
123456789w
123123aa
139.com@163.com
111111q
hao123456
52tiance
19830122
y123456
110119120
1231230
sj811212
13579246810
123.123
superman
789123
12345qwert
770880
js77777
zhangyang
686868
@163.com
imzzhan
xiaoyu
7758521a
abc12345
nihao123
wokaonima
q11111
623623623
989898
122333
13800138000
laopowoaini
787878
123456l
a123123123
198611
332211
tom.com
212121
woaini123456
wanglei
yang123456
zhangqiang
zxcvbnm,./
zhangyan
181818
234567
stryker
167669123
laopo520
2597758
aa5201314
139.com
5201314.
8888888888
74107410
zhanghao
77777777
zhangyu
zzb19860526
qwertyu
5201314qq
198612
q5201314
999888
369852
121121
1122334
123456789asd
123zxc
a123321
QWErtyUIO
456456456
qq000000
m123456
q1w2e3r4t5
woainilaopo
123456789*
131425
liuchang
85208520
zhangjing
c123456
asdfghjk
qq1234
asdzxc
hao123
777888
131131
woainia
beyond
zhang520
556688
123456qw
wangchao
woshiniba
168888
7758991
woshizhu
ainiyiwannian
LAOpo521
abcd123456789
qwerasdf
123456ok
woshinidie
huanhuan
1hxboqg2s
meiyoumima
456321
QQQ123456
1314
898989
123456798
pp.com@163.com
mm123456
123698741
a520520
z321321
asasas
YANG123
584211314
1234561
123456789+
miaomiao
789789789
7788520
AAAAAAa
h123456
3838438
l123456789
198511
ABCDEFG123
zhangjun
123qaz
198512
2525775
54545454
789632145
831213
10101010
xiaohe
19861010
10203
woshishen
0987654321
yj2009
wangqiang
198411
1314520a
xiaowei
123456000
123987
love520
caonimabi
qwe123123
010101
qq666666
789987
10161215
liangliang
qwert123
112112
qianqian
1a2b3c
198410
nuttertools
goodluck
zhangxin
18n28n24a5
liuyang
998877
woxiangni
7788250
a147258369
zhangliang
16897168
223344
123123456
a1b2c3
killer
321123
pp.com
chen123456
wangpeng
753159
775852100
1478963
1213141516
369369369
1236987
123369
12345a
bugaosuni
13145201314520
110112
123456...
JIAOJIAO
100100
1314520123
19841010
7758521123
shangxin
woshiwo
12312300
xingxing
yingying
1233210
34416912
qq12345
qweasd123
nishizhu
19861020
qwe123456789
808080
1310613106
456789123
44444444
123123qq
3141592653
556677
xx123456
jianjian
a1111111
0.123456
198610
loveme
tianshi
woxihuanni
11235813
252525
225588
lovelove
mengmeng
7758258520
xiaoming
shanghai
huyiming
6543210
a7758258
7788414
123456789..
Jordan
nishiwode
ZHUZHU
1314woaini
chenjian
131415
xy123456
123456520
a00000
jiang123
WOAIMAMA
monkey
7418529630
lingling
987456321
w5201314
qwer123456
198412
asdasd123
zzzzzzzz
1q1q1q
741741
987456
19851010
2587758
456654
Iloveyou1314
q12345
imissyou
daniel
aipai
2222222
0147258369
123456789l
q1234567
963963
123123123123
125521
womendeai
baobei520
19861015
667788
000000.
zhangtao
yy123456
chen123
nishishui
789654
liu123
19861212
1230
19841020
wangjun
wangliang
zhangpeng
woainimama
zhangchao
5201314q
19841025
123567
aaaa1111
123456+
134679258
668899
811009
qaz123456789
123456789qwe
111112
130130
19861016
wozhiaini
198712
123...
abcde12345
abcd12345
wanggang
llllll
5121314
456258
125125
qq7758521
369963
987987
142857
poiuytrewq
qqq123
323232
baobei
g227w212
962464
mylove
p1a6s3m
202020
19491001
963258
hhhhhh
2582587758
wangfeng
tiancai
11111111111
summer
wangwang
asd123123
19841024
xinxin
0.0.0.
19861012
19861210
8888888
zhanghui
wenwen
635241
ASDFGHJ
19861023
1234567890.
888168
19861120
tianya
123aaa
111aaa
123456789aaa
8008208820
123123q
football
dandan
www123456789
19861026
qingqing
315315
1111122222
171204jg
19861021
5555555
AS123456789
qqqwww
19861024
yahoo.com
19861225
1qaz1qaz
19871010
1029384756
123258
zxcv123
19861123
1314520.
aidejiushini
123qwe123
198711
operation
19861025
yu123456
19851225
wangshuai
19841015
520521
wangyan
19861011
7007
123456zz
521000
198311
299792458
112211
******
00000
qwer123
51201314
qazwsxedcrfv
LOVE5201314
198312
198510
888888888
1314521521
internet
z123123
a147258
696969
1234321
476730751
5201314789
012345
19861022
welcome
aqwe518951
19861121
HUANGwei
868686
wanghao
NIAIWOMA
xiaojian
19851120
19851212
100000
19841022
zhangbin
shadow
mmmmmm
000...
1357913579
77585217758521
19861216
19841016
az123456
zxcv1234
19841023
wu123456
163163
2008520085
pppppp
789654123
EtnXtxSa65
19851025
woaiwolaopo
ww111111
woaini110
123455
19841026
19881010
www163com
159357456
fangfang
19851015
19861013
19861220
12312
19861018
19861028
a11111111
19841018
119911
AI123456
198211
55555
zhangkai
wangxin
xihuanni
19871024
19861218
16899168
1010110
nimabi
19861125
52013143344
131452000
19871020
freedom
baobao520
winner
123456m
12312312
'''

    lower_pass = lower_pass_txt.split("\n")
    
    for lp in lower_pass:
        if not lp: continue
        if lp == find['username']:
            return False,'当前面板用户名为：{} ，过于简单，存在安全隐患'.format(lp)
        p1 = password_salt(public.md5(lp),uid=1)
        if p1 == find['password']:
            return False,'当前面板密码过于简单，存在安全隐患'
        
        lp  = lp.upper()
        if lp == find['username']:
            return False,'当前面板用户名为：{} ，过于简单，存在安全隐患'.format(lp)
        p1 = password_salt(public.md5(lp),uid=1)
        if p1 == find['password']:
            return False,'当前面板密码过于简单，存在安全隐患'
    
    lower_rule = 'qwertyuiopasdfghjklzxcvbnm1234567890'
    for s in lower_rule:
        for i in range(12):
            if not i: continue
            lp = s * i
            if lp == find['username']:
                return False,'当前面板用户名为：{} ，过于简单，存在安全隐患'.format(lp)
            p1 = password_salt(public.md5(lp),uid=1)
            if p1 == find['password']:
                return False,'当前面板密码过于简单，存在安全隐患'
            
            lp = s.upper() * i
            if lp == find['username']:
                return False,'当前面板用户名为：{} ，过于简单，存在安全隐患'.format(lp)
            p1 = password_salt(public.md5(lp),uid=1)
            if p1 == find['password']:
                return False,'当前面板密码过于简单，存在安全隐患'

    if not is_strong_password(find["password"]):
        return False, '当前面板密码过于简单，存在安全隐患'
    return True,'无风险'

salt = None

def password_salt(password,username=None,uid=None):
    '''
        @name 为指定密码加盐
        @author hwliang<2020-07-08>
        @param password string(被md5加密一次的密码)
        @param username string(用户名) 可选
        @param uid int(uid) 可选
        @return string
    '''
    global salt
    if not salt:
        salt = public.M('users').where('id=?',(uid,)).getField('salt')
        if salt:
            salt = salt[0]
        else:
            salt = ""
    return public.md5(public.md5(password+'_bt.cn')+salt)


def is_strong_password(password):
    """判断密码复杂度是否安全

    非弱口令标准：长度大于等于7，分别包含数字、小写、大写、特殊字符。
    @password: 密码文本
    @return: True/False
    @author: linxiao<2020-9-19>
    """

    if len(password) < 7:
        return False

    import re
    digit_reg = "[0-9]"  # 匹配数字 +1
    lower_case_letters_reg = "[a-z]"  # 匹配小写字母 +1
    upper_case_letters_reg = "[A-Z]"  # 匹配大写字母 +1
    special_characters_reg = r"((?=[\x21-\x7e]+)[^A-Za-z0-9])"  # 匹配特殊字符 +1

    regs = [digit_reg,
            lower_case_letters_reg,
            upper_case_letters_reg,
            special_characters_reg]

    grade = 0
    for reg in regs:
        if re.search(reg, password):
            grade += 1

    if grade == 4 or (grade == 3 and len(password) >= 9):
        return True
    return False
