#!/usr/bin/env python
"""
小红书登录测试脚本

使用真实API测试小红书手机号登录功能
"""
import argparse
import os
import sys
from test_login_real import TestLoginRealApi


def main():
    """运行小红书登录测试"""
    parser = argparse.ArgumentParser(description="测试小红书手机号登录功能")
    parser.add_argument("--phone", help="测试用手机号码")
    parser.add_argument("--area-code", default="+86", help="国家/地区代码，默认+86")
    parser.add_argument("--account", default="18780134977", help="小红书账号，默认18780134977")
    parser.add_argument("--sign-url", default="http://154.89.148.31:5005/sign", help="签名服务URL，默认http://154.89.148.31:5005/sign")
    parser.add_argument("--disable-sign", action="store_true", help="禁用签名服务")
    args = parser.parse_args()
    
    # 设置环境变量
    if args.phone:
        os.environ["XHS_TEST_PHONE"] = args.phone
    if args.area_code:
        os.environ["XHS_TEST_AREA_CODE"] = args.area_code
    
    # 设置账号和签名URL环境变量
    os.environ["XHS_ACCOUNT"] = args.account
    
    if args.disable_sign:
        os.environ["XHS_USE_SIGN"] = "false"
    else:
        os.environ["XHS_USE_SIGN"] = "true"
        os.environ["XHS_SIGN_URL"] = args.sign_url
        
    # 创建测试实例
    test = TestLoginRealApi()
    
    try:
        # 打印使用说明
        print("=" * 60)
        print("小红书手机号登录测试")
        print("=" * 60)
        print(f"账号: {args.account}")
        print(f"签名服务: {'禁用' if args.disable_sign else args.sign_url}")
        print("此测试将执行以下步骤：")
        print("1. 向指定手机号发送验证码")
        print("2. 等待您输入收到的验证码")
        print("3. 使用验证码尝试登录")
        print("4. 检查登录状态")
        print("=" * 60)
        
        # 运行测试
        result = test.test_real_login_flow()
        print("\n✅ 测试成功完成!")
        return 0
    except KeyboardInterrupt:
        print("\n用户中断测试")
        return 1
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 