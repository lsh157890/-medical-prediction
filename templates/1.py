import json
import re


def regenerate_index_mappings(json_path):
    # 加载原始JSON数据
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 提取有效特征码（排除动态生成的特征）
    static_features = [
        key for key in data['feature_mappings']
        if not re.match(r'feature_\(\d+\)', key)
    ]

    # 验证特征数量
    expected_count = 132
    if len(static_features) < expected_count:
        raise ValueError(f"特征数量不足，需要{expected_count}个，当前{len(static_features)}个")

    # 生成新的index_mappings
    new_index = {
        str(idx): feature
        for idx, feature in enumerate(static_features[:expected_count])
    }

    # 更新数据并保存
    data['index_mappings'] = new_index

    # 添加版本控制
    version = data.get('version', '1.0.0').split('.')
    version[-1] = str(int(version[-1]) + 1)
    data['version'] = '.'.join(version)

    # 生成备份文件
    backup_path = json_path.replace('.json', '_bak.json')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # 保存新文件
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=False)

    print(f"生成完成！新增{len(new_index)}个索引映射")
    print(f"版本号更新为：{data['version']}")
    print(f"原始配置已备份至：{backup_path}")

    # 使用示例
    if __name__ == "__main__":
        regenerate_index_mappings('D:/pycharm.py/ScheduleManager/medicStatic/src/configs/medical/features.config.json')