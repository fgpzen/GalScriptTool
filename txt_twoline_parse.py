import re
import json
import argparse
import os

def load_config(config_file):
    if not os.path.exists(config_file):
        print(f"Config file {config_file} not found. Using default rules.")
        return 0, {
            "00_skip": r'^◆.+?◆([\x00-\x7F])',
            "01_search": r'^◆.+?◆(?P<msg>[^「『（].*[^。！？、‥])$',
            "02_search": r'^◆.+?◆(?P<msg>[「『（].*)$',
            "03_search": r'^◆.+?◆(?P<name>[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF].*)$'
        }
    
    rules = {}
    startline = 0
    with open(config_file, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith('startline='):
                startline = int(line.split('=')[1])
            elif '=' in line:
                key, value = line.split('=', 1)
                rules[key.strip()] = value.strip()
            elif line.startswith('sample='):
                break  # Ignore lines after sample=
    return startline, rules

def parse_lines(lines, startline, rules):
    parsed_data = []
    previous_match = {}

    for line_num, line in enumerate(lines):
        if line_num < startline:
            continue

        line = line.strip()

        # 处理00_skip规则
        if "00_skip" in rules and re.match(rules["00_skip"], line):
            continue

        for rule_name in sorted(rules):
            if rule_name == "00_skip":
                continue

            match = re.match(rules[rule_name], line)
            if match:
                match_dict = match.groupdict()
                if "msg" in match_dict:
                    if "msg" in previous_match:
                        parsed_data.append({"message": previous_match["msg"]})
                    previous_match = {"msg": match_dict["msg"]}
                    break
                elif "name" in match_dict:
                    if "name" in previous_match:
                        print(f"Error: Consecutive 'name' found. Previous: {previous_match['name']}, Current: {match_dict['name']}")
                    elif "msg" in previous_match:
                        parsed_data.append({"name": match_dict["name"], "message": previous_match["msg"]})
                        previous_match = {}
                    else:
                        previous_match = {"name": match_dict["name"]}
                    break

    # 处理剩余的未匹配的消息
    if "msg" in previous_match:
        parsed_data.append({"message": previous_match["msg"]})

    return parsed_data

def build_translation_index(output_data, translations):
    name_index = {}
    message_index = {}

    for idx, item in enumerate(output_data):
        if "name" in item:
            name = item["name"]
            if name not in name_index:
                name_index[name] = translations[idx].get("name", "")
        if "message" in item:
            message = item["message"]
            if message not in message_index:
                message_index[message] = translations[idx].get("message", "")

    return name_index, message_index

def replace_lines(lines, startline, rules, name_index, message_index):
    replaced_lines = []
    previous_match = {}

    for line_num, line in enumerate(lines):
        if line_num < startline:
            replaced_lines.append(line)
            continue

        original_line = line

        # 处理00_skip规则
        if "00_skip" in rules and re.match(rules["00_skip"], original_line.strip()):
            replaced_lines.append(line)
            continue

        for rule_name in sorted(rules):
            if rule_name == "00_skip":
                continue

            match = re.match(rules[rule_name], original_line.strip())
            if match:
                match_dict = match.groupdict()
                if "msg" in match_dict:
                    matched_str = match_dict["msg"]
                    if matched_str in message_index:
                        translated_str = message_index[matched_str]
                        line = line.replace(matched_str, translated_str)
                    previous_match = {"msg": matched_str}
                    break
                elif "name" in match_dict:
                    matched_str = match_dict["name"]
                    if matched_str in name_index:
                        translated_str = name_index[matched_str]
                        line = line.replace(matched_str, translated_str)
                    previous_match = {"name": matched_str}
                    break

        replaced_lines.append(line)

    return replaced_lines



def main():
    parser = argparse.ArgumentParser(description="Parse and/or replace text using regex rules and output JSON.")
    parser.add_argument('mode', choices=['extract', 'insert'], help='Mode to run the script in: extract or insert')
    parser.add_argument('-i', '--input', type=str, required=True, help='Input text file to parse or replace')
    parser.add_argument('-o', '--output', type=str, help='Output JSON file to save results (default: input.json)')
    parser.add_argument('-c', '--config', type=str, default='config.ini', help='Configuration file with regex rules (default: config.ini)')
    parser.add_argument('-s', '--startline', type=int, help='Line number to start processing from (overrides config file)')
    parser.add_argument('-t', '--translate', type=str, help='Translation file to use for replacement (default: input.trans.json)')

    args = parser.parse_args()

    # 加载配置文件
    startline, rules = load_config(args.config)

    # 如果命令行参数中提供了 startline，则覆盖配置文件中的值
    if args.startline is not None:
        startline = args.startline

    # 读取输入文件，保留换行符
    with open(args.input, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    if args.mode == 'insert':
        # 替换模式
        translate_file = args.translate if args.translate else args.input.rsplit('.', 1)[0] + '.trans.json'
        output_file = args.output if args.output else args.input.rsplit('.', 1)[0] + '.json'

        # 读取翻译文件
        with open(translate_file, 'r', encoding='utf-8') as file:
            translations = json.load(file)

        # 读取输出文件以获取索引
        with open(output_file, 'r', encoding='utf-8') as file:
            output_data = json.load(file)

        # 建立翻译索引
        name_index, message_index = build_translation_index(output_data, translations)

        # 替换行内容
        replaced_lines = replace_lines(lines, startline, rules, name_index, message_index)

        # 保存替换后的内容，保持原始换行符
        new_file = args.input.rsplit('.', 1)[0] + '.trans.' + args.input.rsplit('.', 1)[1]
        with open(new_file, 'w', encoding='utf-8') as file:
            file.writelines(replaced_lines)

        print(f"Processed and replaced lines starting from line {startline}.")
        print(f"Saved replaced text to {new_file}.")
    else:
        # 提取模式
        parsed_data = parse_lines(lines, startline, rules)

        # 设置默认输出文件名
        output_file = args.output if args.output else args.input.rsplit('.', 1)[0] + '.json'

        # 保存到输出文件
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(parsed_data, file, ensure_ascii=False, indent=4)

        print(f"Processed {len(lines)} lines starting from line {startline}.")
        print(f"Saved results to {output_file}.")

if __name__ == "__main__":
    main()
