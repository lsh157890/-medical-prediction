<template>
  <el-skeleton :rows="6" animated v-if="isLoading" />
  <div class="analysis-container">
    <h2>病例分析结果</h2>

    <!-- 结果概览卡片 -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :span="8">
  <el-card shadow="hover">
    <div class="card-title">风险等级</div>
    <div class="card-value">{{ analysisResult?.risk_level || '--' }}</div>
  </el-card>
</el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="card-title">预测准确率</div>
          <div class="card-value">{{ analysisResult?.accuracy?.toFixed(1) || '--' }}%</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="card-title">建议治疗方案</div>
          <div class="card-value">{{ analysisResult.suggested_treatment || '--' }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 详细图表 -->
    <div class="chart-container">
      <div v-if="!hasAnalysisData" class="empty-tip">
        <el-empty description="未获取到有效分析数据">
          <el-button type="primary" @click="retryLoad">重新加载</el-button>
        </el-empty>
      </div>
      <div class="chart-row">
        <div class="chart-wrapper">
          <h3>特征重要性</h3>
          <div ref="featureChart" style="width: 100%; height: 400px;"></div>
        </div>
        <div class="chart-wrapper">
          <h3>风险分布</h3>
          <div ref="riskChart" style="width: 100%; height: 400px;"></div>
        </div>
      </div>
    </div>
    <div class="data-quality-indicator">
      <el-tag :type="dataQualityType">
        数据可信度: {{ dataQualityScore }}%
      </el-tag>
    </div>
    <div class="detail-container" v-if="!isLoading && hasAnalysisData">
      <h3>详细特征数据</h3>
      <div class="detail-list">
        <div class="detail-item" v-for="f in analysisResult.features || []" :key="f.code">
          <span class="label">{{ f.name }}</span>
          <span class="value">
            {{ f.importance?.toFixed(2) || '--' }}{{ f.unit }}
          </span>
        </div>
      </div>
    </div>
    <div class="sort-controls">
      <el-radio-group v-model="sortKey">
        <el-radio-button value="importance">按重要性排序</el-radio-button>
        <el-radio-button value="name">按名称排序</el-radio-button>
      </el-radio-group>
    </div>
    <div class="data-quality-warning" v-if="hasInvalidData">
      <el-alert type="warning" show-icon>
        <template #title>
          检测到{{ invalidDataCount }}项数据质量问题，
          <el-button type="text" @click="showRawData=!showRawData">
            {{ showRawData ? '隐藏' : '显示' }}原始数据
          </el-button>
        </template>
      </el-alert>

      <pre v-if="showRawData">{{ rawAnalysisData }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick, watch, shallowRef } from 'vue'
import * as echarts from 'echarts'
import medicalFeatures from '@/configs/medical/features.config.json';
import { z } from 'zod';
import { ElMessage } from 'element-plus';
import merge from 'lodash.merge'
import { generateFeatures } from '@/utils/featureProcessor';
import { debounce } from 'lodash-es'

// 在文件顶部声明 loadTimer



const analysisResult = ref({
  risk_level: '--',      // 添加默认值
  accuracy: 0,           // 添加默认值
  suggested_treatment: '数据加载中...',  // 添加默认值
  features: [],
  risk_scores: {
    high: 0,
    medium: 0,
    low: 0
  }
})
let loadTimer = null;


const showRawData = ref(false);

const fileInput = ref(null)

const featureChartInstance = shallowRef(null)
const riskChartInstance = shallowRef(null)
const triggerFileInput = () => {
  fileInput.value?.click() // 安全访问
}
// 在验证逻辑开头添加
if (!medicalFeatures.index_mappings || typeof medicalFeatures.index_mappings !== 'object') {
  console.error('索引映射配置格式错误，重置为空对象')
  medicalFeatures.index_mappings = {}
}

const validateConfig = () => {
  if (!medicalFeatures.index_mappings) {
    medicalFeatures.index_mappings = {}
  }
  if (!medicalFeatures.feature_mappings) {
    medicalFeatures.feature_mappings = {}
  }
  try {
    Object.entries(medicalFeatures.index_mappings).forEach(([indexKey, codes]) => {
      // 确保至少有132个特征
      if (Object.keys(medicalFeatures.index_mappings).length < 132) {
        console.error('特征数量不足，使用默认配置')
        medicalFeatures.index_mappings = Object.fromEntries(
          Array.from({length: 132}, (_,i) => [i, `feature_${i}`])
        )
      }
      // 强制转换为数组
      if (!Array.isArray(codes)) {
        medicalFeatures.index_mappings[indexKey] = [codes].filter(Boolean)
        console.warn(`自动转换索引配置格式: ${indexKey} => ${medicalFeatures.index_mappings[indexKey]}`)
      }

      // 验证数组内容
      medicalFeatures.index_mappings[indexKey] = codes.map(code => {
        if (!medicalFeatures.feature_mappings[code]) {
          console.warn(`缺失特征码映射: ${code}，已自动创建`)
          medicalFeatures.feature_mappings[code] = {
            name: code.replace(/_/g, ' '),
            category: 'auto-generated'
          }
        }
        return code
      })
    })
  } catch (error) {
    console.error('配置验证失败:', error)
    // 降级处理...
    medicalFeatures.index_mappings = {};
    medicalFeatures.feature_mappings = {};
  }
}
在onMounted中调用
onMounted(() => {
  try {
    medicalFeatures.index_mappings = Object.fromEntries(
      Object.entries(medicalFeatures.index_mappings)
        .filter(([key]) => /^\d+$/.test(key))
    );

    validateConfig();
    loadAnalysisResult();
  } catch (error) {
    ElMessage.error(`配置加载失败: ${error.message}`);
    console.error('完整错误信息:', {
      config: medicalFeatures,
      error: error.stack
    });
    // 降级处理
    medicalFeatures.index_mappings = {};
    medicalFeatures.feature_mappings = {};
  }
});
// 在应用初始化时调用


const featureChart = ref(null)
const riskChart = ref(null)




// 从本地存储加载分析结果
console.log('从localStorage加载的原始数据:', localStorage.getItem('lastAnalysisResult'))

const safeDispose = (chartRef) => {
  if (chartRef.value && !chartRef.value.isDisposed) {
    chartRef.value.dispose()
    chartRef.value = null
  }
}

// 防抖重绘函数
const debouncedResize = debounce(() => {
  [featureChartInstance, riskChartInstance].forEach(chartRef => {
    if (chartRef.value?.resize) {
      chartRef.value.resize({
        animation: {
          duration: 300
        }
      })
    }
  })
}, 300)
const getFeatureChartOption = () => ({
  xAxis: {
    type: 'value',
    name: '重要性系数',
    axisLabel: {
      formatter: value => Number(value).toFixed(2),
      color: '#666'
    }
  },
  yAxis: {
    type: 'category',
    data: analysisResult.value.features
      .slice(0, 20)
      .map(f => f.name),
    axisTick: { show: false },
    axisLabel: {
      color: '#333',
      fontSize: 12
    }
  },
  series: [{
    type: 'bar',
    data: analysisResult.value.features
      .slice(0, 20)
      .map(f => Number(f.importance?.toFixed(3)) || 0),
    itemStyle: {
      color: '#4E79A7',
      borderRadius: [0, 5, 5, 0]
    },
    emphasis: {
      itemStyle: {
        shadowBlur: 10,
        shadowColor: 'rgba(0,0,0,0.3)'
      }
    }
  }],
  tooltip: {
    trigger: 'axis',
    formatter: params => {
      const data = params[0]
      return `${data.name}<br/>重要性: ${data.value}`
    }
  }
})
const getRiskChartOption = () => ({
  tooltip: {
    formatter: '{b}: {c}%'
  },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    avoidLabelOverlap: false,
    itemStyle: {
      borderRadius: 6,
      borderColor: '#fff',
      borderWidth: 2
    },
    label: {
      show: true,
      formatter: '{b}: {d}%',
      color: '#333',
      fontSize: 12
    },
    data: [
      {
        value: analysisResult.value.risk_scores.high,
        name: '高风险',
        itemStyle: { color: '#f56c6c' }
      },
      {
        value: analysisResult.value.risk_scores.medium,
        name: '中风险',
        itemStyle: { color: '#e6a23c' }
      },
      {
        value: analysisResult.value.risk_scores.low,
        name: '低风险',
        itemStyle: { color: '#67c23a' }
      }
    ].filter(d => d.value > 0)
  }]
})

// 优化后的初始化方法


const initCharts = () => {
  nextTick(() => {
    // 清理旧实例
    [featureChartInstance.value, riskChartInstance.value].forEach(chart => {
      chart?.dispose?.();
    });

    // 特征图表
    if (featureChart.value && analysisResult.value.features?.length) {
      try {
        featureChartInstance.value = echarts.init(featureChart.value);
        featureChartInstance.value.setOption({
          // ...保持原有配置
          series: [{
            data: analysisResult.value.features
              .filter(f => f.importance > 0.05)
              .slice(0, 20)
              .map(f => f.importance.toFixed(3))
          }]
        });
      } catch (e) {
        console.error('特征图表异常:', e);
      }
    }

    // 风险图表
    if (riskChart.value) {
      try {
        riskChartInstance.value = echarts.init(riskChart.value);
        riskChartInstance.value.setOption({
          // ...保持原有配置
          series: [{
            data: [
              { value: analysisResult.value.risk_scores.high || 0, name: '高风险' },
              { value: analysisResult.value.risk_scores.medium || 0, name: '中风险' },
              { value: analysisResult.value.risk_scores.low || 0, name: '低风险' }
            ]
          }]
        });
      } catch (e) {
        console.error('风险图表异常:', e);
      }
    }
  });
};
console.log('用于渲染的数据:', {
  features: analysisResult.value.features,
  risk_scores: analysisResult.value.risk_scores
})
const clinicalWarnings = computed(() => {
  return analysisResult.value.features.filter(f => {
    return f.category === '未分类体征' ||
           f.name.match(/特征\s\d+/i) ||
           f.importance < 0.05;
  }).map(f => ({
    feature: f.name,
    issue: f.category === '未分类体征' ? '未分类医疗体征' :
           f.importance < 0.05 ? '临床意义不足' : '命名不规范'
  }));
});
const formatUnit = (meta) => {
  if (!meta.unit) return '--';
  return meta.reference ? `${meta.unit}（${meta.reference}）` : meta.unit;
};

const mapFeatures = (features) => {
  return features.map((f, index) => {
    // 防御性访问
    const code = f?.code || medicalFeatures.index_mappings?.[index]?.[0] || `auto_${index}`;

    const meta = medicalFeatures.feature_mappings?.[code] || {
      name: f?.name || `特征${index}`,
      category: '未分类',
      unit: '--'
    };

    return {
      code,
      name: meta.name,
      category: meta.category,
      unit: meta.unit,
      importance: Math.min(1, Math.max(0, f.importance || 0))
    };
  });
};
const normalizeRiskScores = (scores) => {
  const defaultScores = { high: 0, medium: 0, low: 100 };

  // 添加输入类型保护
  if (!scores || typeof scores !== 'object') {
    return defaultScores;
  }

  // 数值安全处理
  const high = Math.min(100, Math.max(0, Number(scores.high) || 0));
  const medium = Math.min(100, Math.max(0, Number(scores.medium) || 0));

  // 计算 low 值并确保总和为100
  const total = high + medium;
  return {
    high,
    medium,
    low: Math.max(0, 100 - total)
  };
};


const handleResize = () => {
  ;[featureChartInstance.value, riskChartInstance.value].forEach(chart => {
    if (chart && !chart.isDisposed) {
      chart.resize({
        width: 'auto',
        height: 'auto'
      })
    }
  })
}
watch(
  () => analysisResult.value,
  (newVal) => {
    if (newVal.features?.length >= 5 && hasRiskScores.value) {
      initCharts()
    }
  },
  { deep: true, flush: 'post' }
)

const getFallbackFeature = (index) => ({
  code: `fallback_${index}`,
  name: `未识别特征#${index+1}`,
  category: '数据异常',
  unit: '--',
  importance: 0,
  _raw: null
})


const FeatureSchema = z.object({
  code: z.string().refine(v =>
    v.startsWith('icd_') ||
    v.startsWith('loinc_') ||
    /^auto_\d+$/.test(v),
    "无效特征码格式"
  ),
  importance: z.number().min(0).max(1)
    .refine(v => v >= 0.01, "临床意义不足"),
  category: z.string().refine(v =>
    !v.includes('未分类'),
    "需明确分类"
  )
});
const sanitizeAnalysisData = (data) => {
  return {
    risk_level: data.risk_level || 'low',
    accuracy: Math.min(100, Math.max(0, data.accuracy || 0)),
    features: (data.features || []).map(f => ({
      ...f,
      name: f.displayName || f.name || `特征_${f.code}`
    })),
    risk_scores: {
      high: data.risk_scores?.high || 0,
      medium: data.risk_scores?.medium || 0,
      low: data.risk_scores?.low || 100 - (data.risk_scores?.high + data.risk_scores?.medium || 0)
    }
  };
};
const AnalysisResultSchema = z.object({
  risk_level: z.enum(['high', 'medium', 'low']),
  accuracy: z.number().min(50).max(100),
  features: z.array(FeatureSchema).min(5),
  risk_scores: z.object({
    high: z.number().min(0).max(100),
    medium: z.number().min(0).max(100),
    low: z.number().min(0).max(100)
  }).refine(s =>
    Math.abs(s.high + s.medium + s.low - 100) <= 5,
    "风险评分总和需接近100%"
  )
});
const isLoading = ref(true);


const validateAnalysisData = (data) => {
  const schema = z.object({
    risk_level: z.enum(['high', 'medium', 'low']),
    accuracy: z.number().min(0).max(100),
    features: z.array(
      z.object({
        code: z.string(),
        name: z.string(),
        importance: z.number().min(0).max(1)
      })
    ),
    risk_scores: z.object({
      high: z.number().min(0).max(100),
      medium: z.number().min(0).max(100),
      low: z.number().min(0).max(100)
    })
  });

  return schema.safeParse(data);
};




const loadAnalysisResult = async () => {
  try {
    isLoading.value = true;

    const rawData = JSON.parse(localStorage.getItem('lastAnalysisResult') || '{}');

    // 深度合并保护
    analysisResult.value = merge(
      {
        risk_level: 'low',
        accuracy: 0,
        suggested_treatment: '需人工复核',
        features: [],
        risk_scores: { high: 0, medium: 0, low: 0 }
      },
      rawData.analysisResult || {}
    )

    // 强制类型转换
    analysisResult.value.risk_level = analysisResult.value.risk_level || 'low'
    analysisResult.value.accuracy = Number(analysisResult.value.accuracy) || 0
    analysisResult.value.suggested_treatment = analysisResult.value.suggested_treatment || '--'
    // 处理risk_scores
    analysisResult.value.risk_scores = {
      high: Math.min(100, Math.max(0, analysisResult.value.risk_scores?.high || 0)),
      medium: Math.min(100, Math.max(0, analysisResult.value.risk_scores?.medium || 0)),
      low: Math.max(0, 100 - (analysisResult.value.risk_scores?.high + analysisResult.value.risk_scores?.medium))
    }
  } catch (error) {
    // 降级处理
    analysisResult.value = {
      risk_level: '--',
      accuracy: 0,
      suggested_treatment: '数据异常',
      features: [],
      risk_scores: { high: 0, medium: 0, low: 100 }
    }
    console.error('数据加载失败:', error);
    analysisResult.value = getDegradedResult();
  } finally {
    isLoading.value = false;
    nextTick(initCharts);
  }
};
// 降级数据展示


const getDegradedResult = () => ({
  risk_level: '--',
  accuracy: 0,
  suggested_treatment: '数据异常，请联系管理员',
  features: Array.from({length: 5}, (_,i) => ({
    code: `err_${i}`,
    name: `数据异常特征#${i}`,
    importance: 0,
    unit: '--'
  })),
  risk_scores: { high: 0, medium: 0, low: 100 }
});
// 辅助函数
const validateRiskLevel = (level) => {
  const validLevels = ['high', 'medium', 'low'];
  return validLevels.includes(level?.toLowerCase()) ? level : '--';
};

const clampValue = (value, min, max) => {
  const num = Number(value) || 0;
  return Math.min(max, Math.max(min, num));
};


const MedicalFeatureSchema = z.object({
  code: z.string().refine(v => v.startsWith('icd_') || v.startsWith('loinc_'), {
    message: "特征代码需符合医疗编码规范"
  }),
  importance: z.number().min(0).max(1)
    .refine(v => v >= 0.01, "临床意义阈值需≥0.01")
});
const getEmptyAnalysisResult = () => ({
  risk_level: '--',
  accuracy: 0,
  suggested_treatment: '--',
  features: [],
  risk_scores: { high: 0, medium: 0, low: 0 }
});
// 添加异步映射方法
const mapFeaturesAsync = (features) => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve(mapFeatures(features));
    }, 50); // 模拟异步处理
  });
};
onMounted(() => {
  window.addEventListener('resize', debouncedResize)
  loadAnalysisResult()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', debouncedResize)
  safeDispose(featureChartInstance)
  safeDispose(riskChartInstance)
})


// 初始化图表
const medicalColorPalette = [
  '#4E79A7', // 消化系统蓝
  '#E15759', // 心血管红
  '#76B7B2', // 神经系统青
  '#F28E2B', // 代谢疾病橙
  '#59A14F', // 感染症状绿
  '#EDC948', // 皮肤症状黄
  '#B07AA1', // 骨骼肌肉紫
  '#FF9DA7', // 呼吸系统粉
  '#9C755F', // 泌尿系统棕
  '#BAB0AC'  // 其他分类灰
];








// 风险等级颜色计算
const riskColor = computed(() => {
  const level = analysisResult.value?.risk_level?.toLowerCase?.() || ''
  return {
    high: '#f56c6c',
    medium: '#e6a23c',
    low: '#67c23a'
  }[level] || '#909399'
})


onBeforeUnmount(() => {
  // 使用value属性访问图表实例
  [featureChartInstance, riskChartInstance].forEach(chartRef => {
    if (chartRef.value && !chartRef.value.isDisposed) {
      chartRef.value.dispose()
      chartRef.value = null
    }
  })
  window.removeEventListener('resize', handleResize)
})




const hasAnalysisData = computed(() => {
  return (
    analysisResult.value.features?.length >= 5 &&  // 至少5个有效特征
    analysisResult.value.accuracy > 50 &&         // 准确率需有效
    Object.values(analysisResult.value.risk_scores || {})
      .some(v => v > 0)
  );
});

const hasRiskScores = computed(() => {
  return Object.values(analysisResult.value.risk_scores || {}).some(v => v > 0)
})
const sortKey = ref('importance')

const sortedFeatures = computed(() => {
  return [...analysisResult.value.features].sort((a, b) => {
    if (sortKey.value === 'importance') {
      return b.importance - a.importance
    }
    return a.name.localeCompare(b.name)
  })
})
const categoryColors = {
  '皮肤症状': '#c23531',
  '全身症状': '#2f4554',
  '消化系统': '#61a0a8',
  '呼吸系统': '#d48265',
  '心血管系统': '#91c7ae',
  '神经系统': '#749f83',
  '代谢疾病': '#ca8622',
  '未分类': '#999'
}
const invalidDataCount = computed(() => {
  // 添加空数组回退
  return (analysisResult.value.features || []).filter(f =>
    (f.name?.includes('特征') ||
    f.category === '未分类') &&
    // 添加重要性的有效性检查
    (isNaN(f.importance) || f.importance <= 0)
  ).length;
});

const hasInvalidData = computed(() => invalidDataCount.value > 0);
const retryLoad = () => {
  isLoading.value = true
  loadAnalysisResult()
}
const dataQualityScore = computed(() => {
  const features = analysisResult.value.features || [];
  const total = features.length;
  if (total === 0) return 0;

  const validCount = features.filter(f =>
    f.importance > 0.05 &&
    f.category !== '未分类' &&
    !f.name.match(/特征\s?\d+/)
  ).length;

  return Math.round((validCount / total) * 100);
});

const dataQualityType = computed(() => {
  const score = dataQualityScore.value;
  if (score > 80) return 'success';
  if (score > 60) return 'warning';
  return 'danger';
});

</script>

<style scoped>
.analysis-container {
  padding: 20px;
}

.overview-cards {
  margin-bottom: 20px;
}

.card-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 10px;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
}

.chart-container {
  position: relative;
  min-height: 420px; /* 确保图表容器有足够高度 */
}

.chart-row {
  display: flex;
  gap: 20px;
}

.chart-wrapper {
  position: relative;
  height: 400px;
  transition: height 0.3s;
}

.chart-wrapper {
  min-height: 400px; /* 确保容器有固定高度 */
  position: relative;
}



@media (max-width: 768px) {
  .chart-row {
    flex-direction: column;

    .chart-wrapper {
      height: 300px;
      min-height: unset;

      h3 {
        font-size: 14px;
      }
    }
  }

  .detail-item {
    flex-wrap: wrap;

    .label, .value {
      width: 100%;
    }
  }
}
/* 加载动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
.chart-wrapper h3 {
  margin-top: 0;
  margin-bottom: 15px;
  color: #333;
}
.analysis-container {
  min-height: 600px;
}

.detail-container {
  margin-top: 30px;
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.detail-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 15px;
  margin-top: 15px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.label {
  color: #606266;
}

.value {
  color: #303133;
  font-weight: 500;
}
.chart-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

/* 优化数据质量警告样式 */
.data-quality-warning {
  margin-top: 20px;
  pre {
    background: #f8f9fa;
    padding: 10px;
    border-radius: 4px;
    max-height: 300px;
    overflow: auto;
  }
}
</style>
