const fs = require('fs');
const path = require('path');

class FeatureMapper {
  constructor() {
    this.mappings = this.loadMappings();
    this.watchFile();
  }

  loadMappings() {
    try {
      const rawData = fs.readFileSync(
        path.join(__dirname, 'features.config.json') // 调整路径
      );
      return JSON.parse(rawData).feature_mappings; // 匹配新结构
    } catch (e) {
      console.error('特征映射加载失败，启用空映射:', e);
      return {_default: {name: '未知指标', unit: ''}};
    }
  }

  // 新增支持完整特征对象映射
  mapFullFeature(feature) {
    const mapping = this.mappings[feature.code] || this.mappings._default;
    return {
      ...feature,
      displayName: mapping.name,
      scientificName: feature.code, // 保留原始字段
      unit: mapping.unit,
      riskLevel: this.calculateRisk(feature.value) // 示例扩展功能
    };
  }

  // 批量处理优化
  batchMap(features) {
    return features.map(f => this.mapFullFeature(f));
  }
}

module.exports = new FeatureMapper();
