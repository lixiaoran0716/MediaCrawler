import requests
import json

# 测试QQ新闻detail类型爬取
def test_qqnews_detail():
    url = "http://127.0.0.1:8000/api/crawl"
    
    # 使用配置文件中的示例URL进行测试
    payload = {
        "platform": "qqnews",
        "type": "detail",
        "keywords": "",
        "start_page": 1,
        "get_comment": False,
        "get_sub_comment": False,
        "save_data_option": "json",
        "login_type": "qrcode",
        "specified_notes": [
            "https://new.qq.com/rain/a/20241201A00J7900",
            "https://new.qq.com/rain/a/20241201A00J8H00"
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    test_qqnews_detail()