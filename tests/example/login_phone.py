import datetime
import json
from http.cookiejar import Cookie
from time import sleep

import qrcode
import requests
from playwright.sync_api import sync_playwright

from xhs import DataFetchError, XhsClient



def sign(uri, data=None, a1="", web_session=""):
    # 填写自己的 flask 签名服务端口地址
    res = requests.post("http://154.89.148.31:5005/sign",
                        json={"uri": uri, "data": data, "a1": a1, "web_session": web_session})
    signs = res.json()
    return {
        "x-s": signs["x-s"],
        "x-t": signs["x-t"]
    }


if __name__ == '__main__':
    Cookie="a1=187d2defea8dz1fgwydnci40kw265ikh9fsxn66qs50000726043;webId=ba57f42593b9e55840a289fa0b755374;gid.sign=PSF1M3U6EBC/Jv6eGddPbmsWzLI=;gid=yYWfJfi820jSyYWfJfdidiKK0YfuyikEvfISMAM348TEJC28K23TxI888WJK84q8S4WfY2Sy;acw_tc=0a50864f17472147403221376e3e8d3210955cf1ba215b86d9874183b8b0bf;web_session=0400698cf3028b57e499cf29113a4bbf5db5a3"
    xhs_client = XhsClient(cookie=Cookie,sign=sign)
    print(datetime.datetime.now())
    qr_res = xhs_client.get_qrcode()
    qr_id = qr_res["qr_id"]
    qr_code = qr_res["code"]

    qr = qrcode.QRCode(version=1, error_correction=qrcode.ERROR_CORRECT_L,
                       box_size=50,
                       border=1)
    qr.add_data(qr_res["url"])
    qr.make()
    qr.print_ascii()

    while True:
        check_qrcode = xhs_client.check_qrcode(qr_id, qr_code)
        print(check_qrcode)
        sleep(1)
        if check_qrcode["code_status"] == 2:
            print(json.dumps(check_qrcode["login_info"], indent=4))
            print("当前 cookie：" + xhs_client.cookie)
            break

    print(json.dumps(xhs_client.get_self_info(), indent=4))