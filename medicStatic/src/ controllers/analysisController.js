const featureMapper = require('../utils/featureMapper');

exports.analyzeCase = async (req, res) => {
  try {
    const mappedResult = {
      ...rawResult,
      features: featureMapper(rawResult.features) // ✅ 关键映射步骤
    };
    res.json(mappedResult);
  } catch (err) {
    console.error('映射失败:', err); // 添加错误日志
  }
}
