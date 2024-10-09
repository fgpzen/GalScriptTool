import requests
import json
import sys

# 将你的 DeepSeek API 密钥设置为默认值
DEFAULT_API_KEY  = '输入你的DeepSeek API'

def get_byte_length(s):
    return len(s) * 2

def modify_sentences(json_path, api_key=DEFAULT_API_KEY):
    # 读取 JSON 文件
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # 设置请求头部
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    # API URL
    url = 'https://api.deepseek.com/chat/completions'

    # 遍历 JSON 数据中的每个条目
    for key, (value, byte_reduction) in data.items():
        # 计算需要减少的汉字数量
        char_reduction = abs(byte_reduction) // 2
        sentence = value

        # 过滤截断的条目，需要缩短的汉字比句子还长
        if byte_reduction + get_byte_length(sentence) <= 0:
            print(f"注意：对于 {key}，需要减少的汉字数量超过句子长度，跳过此条目。")
            continue
        
        # 如果此条目是否已经缩短过，才需要缩短
        if get_byte_length(key) - get_byte_length(sentence) + byte_reduction < 0:
            retries = 0
            while retries < 3:  # 允许最多尝试3次（包括第一次）
                request_data = {
                    'model': 'deepseek-chat',
                    'messages': [
                        {'role': 'system', 'content': '你是一个中文文学大师，可以完成句子的缩写。记住只需要发送修改后的句子，不要发送其他的任何内容。'},
                        {'role': 'user', 'content': f'请帮我将以下中文句子缩短{char_reduction}个字，可以缩短或删除部分汉字或标点符号："{key}"'}  # 用户请求缩短句子的指令
                    ],
                    'stream': False
                }
                
                response = requests.post(url, json=request_data, headers=headers)
                if response.status_code == 200:
                    response_data = response.json()
                    message_content = response_data['choices'][0]['message']['content'].strip('"')
                    # 计算字节差异
                    delta_bytes = get_byte_length(key) - get_byte_length(message_content) + byte_reduction
                    if delta_bytes < 0:
                        #print(f"原句字数{len(key)} 缩短后的字数 {len(message_content)}")
                        #print(f"注意：原句：{key} API返回: {message_content}  未达预期还需缩短{abs(delta_bytes // 2)}个字，将重试第{retries + 1}次 API 请求。")
                        retries += 1
                        continue
                    data[key][0] = message_content
                    break
                else:
                    print(f"Error processing {key}: {response.text}")
                    break
            if retries == 3:
                print(f"重试失败：{key} API返回: {message_content} 缩短尝试{retries}次失败，未能成功缩短句子，跳过此条目。")
        # else:
        #     print(f"不需要修改：{key} ，已缩短过 {char_reduction} 字，跳过此条目。")

    with open(json_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    print("所有句子的处理已完成。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py json_path api_key")
    else:
        json_path = sys.argv[1]
        api_key = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_API_KEY
        modify_sentences(json_path, api_key)
