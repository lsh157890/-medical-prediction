import medicalFeatures from '@/configs/medical/features.config.json';


// export const generateFeatures = (complaint, diagnosis) => {
//   const features = new Array(Object.keys(medicalFeatures.index_mappings).length.fill(0));
//   // 动态生成症状映射
//   const symptomMap = Object.entries(medicalFeatures.index_mappings).reduce((map, [index, code]) => {
//     const symptom = medicalFeatures.feature_mappings[code]?.name;
//     if (symptom) {
//       map[symptom] = parseInt(index);
//     }
//     return map;
//   }, {});
//
//   // 自动匹配症状
//   Object.entries(symptomMap).forEach(([symptom, index]) => {
//     const regex = new RegExp(symptom, 'i');
//     if (regex.test(complaint)) features[index] = 1;
//     if (regex.test(diagnosis)) features[index] = 1;
//   });
//
//   return features;
// };
export const generateFeatures = (complaint, diagnosis) => {
  try {
    // 输入校验
    const validComplaint = String(complaint || '').slice(0, 500); // 限制长度
    const validDiagnosis = String(diagnosis || '').slice(0, 300);

    // 初始化特征数组时添加保护
    const features = Array.from({ length: 132 }, () => 0);

    // ...原有处理逻辑...
    const symptomMap = Object.entries(medicalFeatures.index_mappings).reduce((map, [index, code]) => {
      const symptom = medicalFeatures.feature_mappings[code]?.name;
      if (symptom) {
        map[symptom] = parseInt(index);
      }
      return map;
    }, {});

    // 自动匹配症状
    Object.entries(symptomMap).forEach(([symptom, index]) => {
      const regex = new RegExp(symptom, 'i');
      if (regex.test(complaint)) features[index] = 1;
      if (regex.test(diagnosis)) features[index] = 1;
    });
    // 最终校验
    if (features.length !== 132 || features.some(v => ![0, 1].includes(v))) {
      console.error('特征生成异常，返回安全值');
      return new Array(132).fill(0);
    }

    return features;
  } catch (error) {
    console.error('特征生成失败:', error);
    return new Array(132).fill(0); // 返回安全默认值
  }
}



export const validateFeatures = (features) => {
  return features.every(f => typeof f === 'number' && (f === 0 || f === 1));
};
