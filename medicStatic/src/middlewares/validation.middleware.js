const validateFeatures = (req, res, next) => {
  try {
    const rawFeatures = res.locals.analysisResult?.features || [];

    // 严格校验每个特征
    const validatedFeatures = rawFeatures.map((f, index) => {
      const code = f.code?.trim() || `feature_${index}`;

      return {
        code,
        name: f.name?.trim() || code, // 默认使用code作为name
        importance: Math.max(0, Number(f.importance) || 0),
        unit: f.unit?.trim() || '单位未定义',
        category: f.category?.trim() || '未分类',
        // 添加校验元数据
        _validated: true,
        _originalIndex: index
      };
    });

    // 查找未通过校验的特征
    const invalidFeatures = validatedFeatures.filter(f =>
      f.code.startsWith('feature_') || f.unit === '单位未定义'
    );

    if (invalidFeatures.length > 0) {
      console.warn('发现未定义特征:', invalidFeatures);
    }

    res.locals.analysisResult.features = validatedFeatures;
    next();
  } catch (e) {
    next(e);
  }
}
