
<template>
  <div class="main-container">
    <input
        type="file"
        ref="fileInput"
        hidden
        accept="image/*"
        @change="handleFileChange"
      >
    <!-- 右侧主区域 -->
    <div class="main-content">
      <!-- 顶部操作栏 -->
      <el-header>
        <el-input
          v-model="searchKey"
          placeholder="点此搜索"
          style="width: 300px"
        />
        <el-dialog v-model="showCropper" title="裁剪头像">
          <div class="cropper-container">
            <img ref="imageRef" :src="tempAvatar" style="max-width: 100%"  @load="handleImageLoaded">
          </div>
          <template #footer>
            <el-button @click="showCropper = false">取消</el-button>
            <el-button type="primary" @click="confirmCrop">确认</el-button>
          </template>
        </el-dialog>
        <!-- 用户信息下拉 -->
        <el-dropdown
          trigger="click"
          placement="bottom-end"
          @command="handleCommand"
        >
          <div class="user-panel">
            <el-avatar :src="userStore.user?.user_pic || defaultAvatar" />
            <span class="username">
              {{ userStore.username }}  <!-- 使用计算属性 -->
            </span>
            <el-icon><ArrowDown /></el-icon>
          </div>


          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><User /></el-icon>基本资料
              </el-dropdown-item>
              <el-dropdown-item command="avatar" @click.prevent.stop="triggerFileInput">
                <el-icon><Crop /></el-icon>更换头像
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <!-- 病例表单 -->
      <el-main>
        <el-card>
          <el-form :model="form" label-width="120px">
            <el-form-item label="病例信息">
              <div class="patient-info-group">
                <el-input
                  v-model="form.name"
                  placeholder="患者姓名"
                  style="width: 200px; margin-right: 10px"
                />
                <el-select
                  v-model="form.gender"
                  placeholder="性别"
                  style="width: 120px; margin-right: 10px"
                >
                  <el-option label="男" value="male" />
                  <el-option label="女" value="female" />
                </el-select>
                <el-input-number
                  v-model="form.age"
                  :min="0"
                  :max="120"
                  placeholder="年龄"
                  controls-position="right"
                />
              </div>
            </el-form-item>
            <el-form-item value="主诉" label="主诉">
              <el-input
                v-model="form.complaint"
                type="textarea"
                :rows="3"
                placeholder="请输入患者主诉"
              />
            </el-form-item>

            <el-form-item value="初步诊断" label="初步诊断">
              <el-input
                 v-model="form.diagnosis"
                type="textarea"
                :rows="3"
                placeholder="请输入初步诊断"
              />
            </el-form-item>

            <el-form-item label="治疗方案">
                <el-input
                   v-model="form.treatment"
                  type="textarea"
                  :rows="3"
                  placeholder="请输入治疗方案"
                />
            </el-form-item>

            <el-button type="primary" @click="submit">提交病例</el-button>
              <el-card class="case-list" v-if="cases.length > 0">
                <h3>已提交病例</h3>
                <div class="scroll-container">
                  <el-table
                    :data="cases"
                    style="width: 100%"
                    max-height="400"
                    empty-text="暂无病例数据"
                  >
                    <el-table-column prop="id" label="病例编号" width="150"/>
                    <el-table-column prop="date" label="提交时间" width="180" />
                    <el-table-column prop="name" label="患者姓名" />
                    <el-table-column prop="complaint" label="主诉" show-overflow-tooltip />
                    <el-table-column prop="treatment" label="治疗方案" />
                    <el-table-column label="操作" width="180">
                      <template #default="{ row }">
                        <el-button
                          type="primary"
                          size="small"
                          color="silver"
                          :disabled="!validateCase(row)"
                          @click="analyzeCase(row)"
                        >
                          分析
                        </el-button>
                        <el-button
                          type="danger"
                          size="small"
                          @click="deleteCase(row.id, $index)"
                        >
                          删除
                      </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-card>
          </el-form>
        </el-card>
      </el-main>
    </div>
  </div>
  <div class="analysis-container">
  <div v-if="chartLoading" class="chart-loading">
    <el-icon class="is-loading"><Loading /></el-icon>
    图表加载中...
  </div>
  <template v-else>
    <div v-if="analysisResult.features.length" ref="featureChart"></div>
    <div v-else class="no-data">暂无有效分析数据</div>
  </template>
</div>
</template>

<script setup>
import { ref, nextTick, onMounted,onUnmounted, watch,computed  } from 'vue'
import { useRouter } from 'vue-router'
import { userUserStore } from '@/stores/user'
import {
  Document,
  DataAnalysis,
  ArrowDown,
  SwitchButton,
  User,
  Crop,
  EditPen
} from '@element-plus/icons-vue'
import defaultAvatar from '@/assets/default.jpg';
import { ElMessage, ElMessageBox } from 'element-plus'
import 'cropper/dist/cropper.css'
import Cropper from 'cropperjs';
import 'cropperjs/dist/cropper.css';
import medicalFeatures from '@/configs/medical/features.config.json';
import { Loading } from '@element-plus/icons-vue'
import merge from 'lodash.merge'

const showCropper = ref(false)
const tempAvatar = ref('')
const imageRef = ref(null)
let cropperInstance = null
// 添加文件输入引用
const fileInput = ref(null)
let featureChartInstance = null;
const featureChart = ref(null)


const analysisResult = ref({
  risk_level: '',
  accuracy: 0,
  suggested_treatment: '',
  features: [],
  risk_scores: { high: 0, medium: 0, low: 0 }
})
const triggerFileInput = () => {
  nextTick(() => {
    if (fileInput.value) {
      fileInput.value.click()
    }
  })
}

const abortController = ref(new AbortController())

const caseIdCounter = ref(1)
const cases = ref([])


onUnmounted(() => {
  if (abortController.value) {
    abortController.value.abort();
  }
})

const handleFileChange = async (e) => {
  try {
    const file = e.target.files[0];
    if (!file) return;

    // 添加文件类型验证
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      ElMessage.error('仅支持JPEG/PNG格式');
      return;
    }

    // 添加文件大小验证
    if (file.size > 2 * 1024 * 1024) {
      ElMessage.error('图片大小不能超过2MB');
      return;
    }

    // 使用URL.createObjectURL创建临时URL
    if (tempAvatar.value.startsWith('blob:')) {
      URL.revokeObjectURL(tempAvatar.value);
    }
    tempAvatar.value = URL.createObjectURL(file);
    showCropper.value = true;

    // 重置文件输入
    e.target.value = '';
  } catch (error) {
    ElMessage.error(`文件处理失败: ${error.message}`);
  }
};
const handleImageLoaded = () => {
  nextTick(() => {
    try {
      // 销毁旧实例
      if (cropperInstance) {
        cropperInstance.destroy();
      }

      // 初始化新实例
      cropperInstance = new Cropper(imageRef.value, {
        aspectRatio: 1,
        viewMode: 1,
        checkCrossOrigin: true,
        ready() {
          console.log('Cropper初始化完成');
        }
      });
    } catch (error) {
      console.error('Cropper初始化失败:', error);
      ElMessage.error('图片编辑器初始化失败');
      showCropper.value = false;
    }
  });
};
watch(showCropper, (newVal) => {
  if (!newVal && tempAvatar.value.startsWith('blob:')) {
    URL.revokeObjectURL(tempAvatar.value);
    tempAvatar.value = '';
  }
});

onUnmounted(() => {
  if (tempAvatar.value.startsWith('blob:')) {
    URL.revokeObjectURL(tempAvatar.value);
  }
});
const confirmCrop = async () => {
  try {
    if (!cropperInstance) {
      throw new Error('图片编辑器未初始化');
    }

    // 获取裁剪后的Canvas
    const canvas = cropperInstance.getCroppedCanvas({
      width: 256,
      height: 256,
      fillColor: '#fff'
    });

    if (!canvas) {
      throw new Error('无法获取裁剪结果');
    }

    // 转换为Base64
    const base64 = canvas.toDataURL('image/png');

    // 更新用户信息
    userStore.setUser({
      ...userStore.user,
      user_pic: base64
    });

    // 关闭对话框
    showCropper.value = false;
    ElMessage.success('头像更新成功');

    // 释放对象URL
    if (tempAvatar.value.startsWith('blob:')) {
      URL.revokeObjectURL(tempAvatar.value);
    }
  } catch (error) {
    console.error('头像裁剪失败:', error);
    ElMessage.error(`头像保存失败: ${error.message}`);
  } finally {
    // 清理资源
    if (cropperInstance) {
      cropperInstance.destroy();
      cropperInstance = null;
    }
  }
};

const uploadAvatar = async (file) => {
  try {
    const formData = new FormData()
    formData.append('avatar', file)

    const { data } = await axios.post('/api/upload-avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'Authorization': `Bearer ${userStore.token}`
      }
    })

    userStore.setAvatar(data.url)
  } catch (error) {
    throw new Error('上传失败')
  }
}


// 文件转Base64工具函数
const readFileAsDataURL = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    const abortHandler = () => {
      reader.abort()
      reject(new DOMException('Aborted'))
    }

    abortController.signal.addEventListener('abort', abortHandler)

    reader.onload = () => {
      abortController.signal.removeEventListener('abort', abortHandler)
      resolve(reader.result)
    }

    reader.onerror = (error) => {
      abortController.signal.removeEventListener('abort', abortHandler)
      reject(error)
    }

    reader.readAsDataURL(file)
  })
}



const userStore = userUserStore()
const router = useRouter()
const searchKey = ref('') // 定义搜索关键词

const form = ref({
  name: '',
  gender: '',
  age: null,
  complaint: '',
  diagnosis: '',
  treatment: ''
})
const diagnoses = [
  { value: 'hypertension', label: '高血压' },
  { value: 'diabetes', label: '糖尿病' }
]

const treatmentOptions = [
  { value: 'medicine', label: '药物治疗' },
  { value: 'surgery', label: '手术治疗' }
]

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.removeToken()
    router.push('/login')
  } else if (command === 'profile') {
    // 确保路由配置中存在 '/user/profile' 路径
    router.push('/user/profile')
  } else if (command === 'avatar') {
    triggerFileInput()
  }
}
// 初始化计数器

localStorage

onMounted(() => {
  // 检查特征配置
  const featureKeys = Object.keys(medicalFeatures.index_mappings);
  if (featureKeys.length !== 132) {
    ElMessage.error(`特征配置异常，当前特征数: ${featureKeys.length}`);
    console.error('无效的特征配置:', {
      expected: 132,
      actual: featureKeys.length,
      sample: featureKeys.slice(0, 5)
    });
  }

  // 示例输出验证
  console.log('特征配置验证:', {
    index_mappings_type: typeof medicalFeatures.index_mappings,
    feature_mappings_count: Object.keys(medicalFeatures.feature_mappings).length
  });
});




const generateFeatures = (complaint, diagnosis) => {
  try {
    // 初始化特征数组
    const features = new Array(132).fill(0)

    // 空输入处理
    const strComplaint = String(complaint || '').toLowerCase()
    const strDiagnosis = String(diagnosis || '').toLowerCase()
    if (!strComplaint && !strDiagnosis) return features

    // 安全获取特征映射
    const safeMappings = medicalFeatures.index_mappings || {}
    const validCodes = Object.values(safeMappings).filter(
      code => typeof code === 'string' && medicalFeatures.feature_mappings[code]
    )

    // 构建关键词映射
    const keywordMap = validCodes.reduce((map, code) => {
      const config = medicalFeatures.feature_mappings[code]
      const keywords = [
        code.toLowerCase(),
        config.name.toLowerCase(),
        ...(config.cn_keywords || []).map(k => k.toLowerCase())
      ]

      keywords.forEach(keyword => {
        if (!map.has(keyword)) {
          map.set(keyword, code)
        }
      })
      return map
    }, new Map())

    // 文本处理
    const medicalText = `${strComplaint} ${strDiagnosis}`
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^\w\u4e00-\u9fa5]/g, ' ')
      .toLowerCase()

    // 特征匹配
    keywordMap.forEach((code, keyword) => {
      if (new RegExp(`\\b${keyword}\\b`).test(medicalText)) {
        const index = Object.values(safeMappings).indexOf(code)
        if (index >= 0 && index < 132) {
          features[index] = 1
        }
      }
    })
    if (!validateFeatures(features)) {
      console.warn('生成的特征验证失败，使用降级方案')
      return medicalFeatures.default_features || new Array(132).fill(0)
    }
    return features
  } catch (error) {
    console.error('特征生成失败:', error)
    return new Array(132).fill(0) // 返回安全值
  }
}
window.addEventListener('error', (event) => {
  console.error('全局错误捕获:', {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    stack: event.error?.stack
  });
});
// 主入口文件添加
window.addEventListener('unhandledrejection', event => {
  console.error('未处理的Promise拒绝:', event.reason);
  event.preventDefault();
});

window.addEventListener('error', event => {
  console.error('全局错误:', event.error);
  event.preventDefault();
});
const validateCase = (caseData) => {
  return [
    caseData?.id,
    caseData?.complaint?.length > 5,
    caseData?.features?.length === 132
  ].every(Boolean);
};
// 添加性能监控
const perfObserver = new PerformanceObserver(list => {
  list.getEntries().forEach(entry => {
    console.log('[性能监控]', entry.name, `${entry.duration.toFixed(2)}ms`);
  });
});
perfObserver.observe({ entryTypes: ['measure'] });

const submit = () => {
    if (
    !form.value.name?.trim() ||
    !form.value.gender ||
    !form.value.age ||
    !form.value.complaint?.trim()
  ) {
    ElMessage.error('请填写完整的患者信息（姓名、性别、年龄）和主诉')
    return
  }
  if (form.value.age < 0 || form.value.age > 120) {
    ElMessage.error('年龄应在0-120岁之间')
    return
  }
  if (!validateCase(form.value)) {
    ElMessage.error('无效的病例数据');
    return;
  }
  // 增强表单验证
  if (!form.value.name?.trim() || !form.value.complaint?.trim()) {
    ElMessage.error('请填写患者姓名和主诉')
    return
  }
  try {
    // 先生成ID再创建对象
    const timestamp = Date.now().toString().slice(-4)
    const caseId = `CASE-${caseIdCounter.value.toString().padStart(3, '0')}-${timestamp}`
    if (!/[\u4e00-\u9fa5]/.test(form.value.complaint) || form.value.complaint.length < 5) {
      ElMessage.error('主诉需包含中文且不少于5个字符');
      return;
    }
    // 再创建病例对象
    const newCase = {
      id: caseId,
      date: new Date().toLocaleString(),
      name: form.value.name,
      gender: form.value.gender,
      age: form.value.age,
      complaint: form.value.complaint,
      diagnosis: form.value.diagnosis,
      treatment: form.value.treatment,
      features: generateFeatures(form.value.complaint, form.value.diagnosis)
    }

    if (newCase.features.filter(v => v === 1).length === 0) {
      console.error('生成的特征数组全零异常:', {
        complaint: form.value.complaint,
        diagnosis: form.value.diagnosis,
        features: newCase.features
      });
      ElMessage.error('未能识别有效症状特征，请检查主诉和诊断描述');
      return;
    }
    if (!Array.isArray(newCase.features) || newCase.features.length !== 132) {
      console.error('无效特征数组:', newCase);
      throw new Error('无法保存病例：特征数据异常');
    }
    // 更新数据
    cases.value = [newCase, ...cases.value] // 新病例显示在最前面
    caseIdCounter.value++
    localStorage.setItem('caseIdCounter', caseIdCounter.value)

    // 重置表单
    form.value = {
      name: '',
      complaint: '',
      diagnosis: '',
      treatment: ''
    }

    // 打印特征详情
    console.log('生成的特征数组详情:', {
      nonZeroIndices: newCase.features
        .map((v, i) => v === 1 ? i : -1)
        .filter(i => i !== -1),
      matchedSymptoms: medicalFeatures.feature_mappings
    });
    ElMessage.success(`病例 ${caseId} 提交成功`)

    // 保存到本地存储
    localStorage.setItem('cases', JSON.stringify(cases.value.map(c => ({
      ...c,
      features: Array.isArray(c.features) ? c.features : []
    }))))
    localStorage.setItem('caseIdCounter', caseIdCounter.value)
  } catch (error) {
    ElMessage.error(`病例提交失败: ${error.message}`)
    console.error('病例提交失败:', error)
    return;
  }
}

onMounted(() => {
  try {
    const savedCases = localStorage.getItem('cases');
    if (savedCases) {
      cases.value = JSON.parse(savedCases).map(item => ({
        ...item,
        features: Array.isArray(item.features) ?
                 item.features.slice(0, 132) :
                 new Array(132).fill(0)
      }));

      // 新增验证
      cases.value.forEach(c => {
        if (!validateFeatures(c.features)) {
          console.warn('发现无效病例特征，已重置:', c.id);
          c.features = generateFeatures(c.complaint, c.diagnosis);
        }
      });
    }
  } catch (e) {
    console.error('病例数据恢复失败:', e);
    localStorage.removeItem('cases');
  }
});
// 添加窗口resize监听
const handleResize = () => {
  const charts = [featureChartInstance];
  charts.forEach(chart => {
    try {
      if (chart && !chart.isDisposed()) {
        chart.resize({
          width: 'auto',
          height: 'auto'
        });
      }
    } catch (e) {
      console.warn('图表resize失败:', e);
    }
  });
};


// 验证函数增强
// const validateFeatureConfig = () => {
//   const errors = [];
//
//   // 索引类型验证
//   Object.entries(medicalFeatures.index_mappings).forEach(([index, code]) => {
//     if (typeof code !== 'string') {
//       errors.push(`索引${index}类型错误，应为string，实际为${typeof code}`);
//     }
//     if (!medicalFeatures.feature_mappings[code]) {
//       errors.push(`特征码'${code}'未在feature_mappings中定义`);
//     }
//   });
//
//   // 总数验证
//   if (Object.keys(medicalFeatures.index_mappings).length !== 132) {
//     errors.push(`特征总数应为132，实际为${Object.keys(medicalFeatures.index_mappings).length}`);
//   }
//
//   if (errors.length > 0) {
//     console.error("配置验证失败:", errors);
//     throw new Error("特征配置异常");
//   }
// }
// 修改validateFeatureConfig函数
const validateFeatureConfig = () => {
  try {
    if (!medicalFeatures?.index_mappings || !medicalFeatures?.feature_mappings) {
      throw new Error('特征配置结构异常')
    }

    const entries = Object.entries(medicalFeatures.index_mappings)
    if (entries.length !== 132) {
      throw new Error(`特征数量应为132，当前为${entries.length}`)
    }

    entries.forEach(([index, code]) => {
      if (!medicalFeatures.feature_mappings[code]) {
        throw new Error(`特征码${code}在index_mappings中存在但未定义`)
      }
    })
  } catch (error) {
    console.error('特征配置验证失败:', error)
    // 启用安全模式
    medicalFeatures.index_mappings = Object.fromEntries(
      Array.from({length: 132}, (_,i) => [i, `feature_${i}`])
    )
    medicalFeatures.feature_mappings = Object.fromEntries(
      Array.from({length: 132}, (_,i) => [
        `feature_${i}`,
        { name: `动态体征#${i}`, category: "未分类" }
      ])
    )
  }
}
// 添加hasAnalysisData计算属性
const hasAnalysisData = computed(() => {
  return (
    analysisResult.value.features?.length >= 5 &&
    analysisResult.value.accuracy > 50 &&
    (analysisResult.value.risk_scores.high > 0 ||
     analysisResult.value.risk_scores.medium > 0 ||
     analysisResult.value.risk_scores.low > 0)
  )
})
const loadAnalysisResult = async () => {
  try {
    const rawData = JSON.parse(localStorage.getItem('lastAnalysisResult') || '{}');
    const isValid = [
      'analysisResult' in rawData,
      Array.isArray(rawData.analysisResult?.features),
      'risk_level' in rawData.analysisResult
    ].every(Boolean);
    analysisResult.value = merge({
      risk_level: 'low',
      accuracy: 0,
      features: [],
      risk_scores: { high: 0, medium: 0, low: 0 }
    }, rawData.analysisResult);

    // 数值范围约束
    analysisResult.value.accuracy = Math.min(100, Math.max(0, analysisResult.value.accuracy));
    if (!isValid) {
      throw new Error('本地存储数据格式异常');
    }
    // 数据校验
    if (!rawData.analysisResult?.features) {
      throw new Error('分析数据缺失');
    }

    // 更新分析结果
    analysisResult.value = rawData.analysisResult;

    // 风险评分标准化
    const total = Object.values(rawData.analysisResult.risk_scores).reduce((a,b)=>a+b,0);
    if(total !== 100){
      analysisResult.value.risk_scores = {
        high: Math.floor(rawData.analysisResult.risk_scores.high/total*100),
        medium: Math.floor(rawData.analysisResult.risk_scores.medium/total*100),
        low: 100 - Math.floor(rawData.analysisResult.risk_scores.high/total*100)
               - Math.floor(rawData.analysisResult.risk_scores.medium/total*100)
      }
    }
  } catch (error) {
    ElMessage.error('分析数据加载失败: ' + error.message);
    console.error(error);
  }
};
onMounted(() => {
  try {
    // 添加特征配置验证
    validateFeatureConfig()

    // 初始化图表
    initCharts()
  } catch (error) {
    console.error('组件初始化失败:', error)
    ElMessage.error('初始化失败: ' + error.message)
  }
})



const deleteCase = (caseId, index) => {
  ElMessageBox.confirm(
    `确定要删除病例 ${caseId} 吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
  .then(() => {
    // 从数组中移除
    cases.value.splice(index, 1)
    // 更新本地存储
    localStorage.setItem('cases', JSON.stringify(cases.value))
    ElMessage.success('病例删除成功')
  })
  .catch(() => {
    // 用户点击了取消
    ElMessage.info('已取消删除')
  })
}


const chartLoading = ref(true)

const initCharts = () => {
  chartLoading.value = true;

  try {
    // [featureChartInstance, riskChartInstance].forEach(instance => {
    //   if (instance && !instance.isDisposed()) {
    //     instance.dispose();
    //   }
    // });

    if (featureChartInstance) {
      featureChartInstance.dispose();
    }
    if (featureChart.value && analysisResult.value.features?.length) {
      featureChartInstance = echarts.init(featureChart.value);
      // ...保持原有图表配置...
      featureChartInstance.setOption({
          xAxis: {
            type: 'value',
            name: '重要性系数',
            axisLabel: { formatter: value => value.toFixed(2) }
          },
          yAxis: {
            type: 'category',
            data: analysisResult.value.features
              .slice(0, 20)
              .map(f => f.name),
            axisTick: { show: false }
          },
          series: [{
            type: 'bar',
            data: analysisResult.value.features
              .slice(0, 20)
              .map(f => f.importance?.toFixed(3)),
            itemStyle: {
              color: '#4E79A7'
            }
          }]
        });
    }


    chartLoading.value = false;
  } catch (error) {
    console.error('图表初始化失败:', error);
    chartLoading.value = false;
    ElMessage.error('图表初始化失败');
  }
};
const validateFeatures = (features) => {
  return Array.isArray(features) &&
    features.length === 132 &&
    features.every(v => [0, 1].includes(v)) &&
    features.some(v => v === 1) // 至少包含一个有效特征
}


const analyzeCase = async (row) => {
  if (!row || typeof row !== 'object') {
      throw new Error('无效的病例数据');
    }
  if (!row?.id) {
    ElMessage.error('无效的病例数据')
    return
  }
  let requestBody;
  let requestId;
  let controller = null;
  let features = [];
  try {

    controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    const rawFeatures = row.features ?? [];
    const safeComplaint = row.complaint?.trim() ?? ''
    const safeDiagnosis = row.diagnosis?.trim() ?? ''
    // features = Array.isArray(rawFeatures) && rawFeatures.length === 132
    //   ? [...rawFeatures]
    //   : generateFeatures(row.complaint || '', row.diagnosis || '');
    //
    // // 类型强制转换
    // features = features.map(v => Number(v) > 0 ? 1 : 0).slice(0, 132);
    if (controller.signal.aborted) {
        throw new Error('用户取消了请求');
      }

    if (!validateFeatures(features)) {
      throw new Error('生成的特征数据无效');
    }
    if (Array.isArray(rawFeatures) && rawFeatures.length === 132) {
      features = [...rawFeatures]
    } else {
      // 添加生成特征时的空值保护
      features = generateFeatures(safeComplaint || '无主诉', safeDiagnosis || '无诊断')
    }
    if (!Array.isArray(features) || features.length !== 132) {
        console.error('最终特征数组异常，使用降级处理', {
          original: row,
          generated: features
        })
        features = new Array(132).fill(0)
      }
    // 长度补齐
    if (features.length < 132) {
      features = [...features, ...new Array(132 - features.length).fill(0)];
    }

    // 二次验证特征数组
    if (!Array.isArray(features) || features.length !== 132) {
      console.error('非法特征数组:', {
        received: features,
        expectedLength: 132
      });
      features = new Array(132).fill(0); // 降级处理
    }
    console.assert(
      Array.isArray(features) && features.length === 132,
      '特征数组验证失败',
      { features }
    );
    // 二次验证特征数组
    if (!Array.isArray(features) || features.length !== 132) {
      throw new Error('特征数组格式异常');
    }

    // 在请求体中明确使用 feature_vector 字段
    requestBody = {
          feature_vector: features.filter(v => [0, 1].includes(v)),
          case_id: row.id || 'unknown_case'
        };
    console.assert(
        requestBody.feature_vector.length === 132,
        '特征向量长度异常',
        requestBody
      );
     if (!row.complaint?.trim() || !row.diagnosis?.trim()) {
      ElMessage.error('病例数据不完整');
      return;
    }

         // 生成特征数组
    // const features = new Array(132).fill(0);
    // features[0] = Math.min(500, row.complaint.length);
    // features[1] = Math.min(300, row.diagnosis.length);
    features = row.features || generateFeatures(row.complaint, row.diagnosis);
   if (!validateFeatures(features)) {
      console.error('无效特征数组:', features);
      throw new Error('特征数据校验失败');
    }
    requestId = crypto.randomUUID();
    // 生成唯一请求ID
    console.log('Sending feature_vector:', {
      feature_vector: features,
      length: features.length,
      type: typeof features
    });

    console.log('[DEBUG] 特征数组详情:', {
      length: features.length,
      nonZeroCount: features.filter(v => v !== 0).length,
      sample: features.slice(0, 10) // 查看前10个特征
    });
    if (!Array.isArray(features)) {
      throw new Error('特征数据非数组类型');
    }
    if (features.length !== 132) {
      throw new Error(`特征数组长度异常: ${features.length}`);
    }

    requestBody = {
      feature_vector: features.filter(v => [0, 1].includes(v))
    };

    if (!requestBody.feature_vector ||
        requestBody.feature_vector.length !== 132 ||
        requestBody.feature_vector.some(v => ![0, 1].includes(v))) {
      console.error('无效特征数组:', {
        received: requestBody.feature_vector,
        validLength: 132,
        invalidValues: requestBody.feature_vector.filter(v => ![0, 1].includes(v))
      });
      throw new Error('特征数据校验失败');
    }
    if (!requestBody.features ||
        requestBody.features.length !== 132 ||
        requestBody.features.some(v => v !== 0 && v !== 1)) {
        console.error('无效的特征数组:', {
            received: requestBody.features,
            validLength: 132,
            invalidValues: requestBody.features.filter(v => v !== 0 && v !== 1)
        });
        throw new Error('特征数据校验失败');
    }
    console.log('特征数组验证:', {
      length: features.length,
      sum: features.reduce((a,b) => a+b, 0),
      samplePositions: features
        .map((v,i) => v === 1 ? i : -1)
        .filter(i => i !== -1)
        .slice(0, 5)
    });

    // 添加更严格的请求体验证
    if (!Array.isArray(features) ||
        features.length !== 132 ||
        features.some(v => ![0, 1].includes(v))) {
      console.error('非法特征数组:', {
        type: Object.prototype.toString.call(features),
        length: features?.length,
        invalidValues: features?.filter(v => ![0,1].includes(v))
      });
      throw new Error('特征数据格式异常');
    }
    if (!features || !Array.isArray(features) || features.length !== 132) {
      console.error('无效的特征数组:', features);
      ElMessage.error('病例数据分析失败：特征数据异常');
      return;
    }
    // 添加请求头验证
    const headers = new Headers({
      'Content-Type': 'application/json',
      'X-Request-ID': crypto.randomUUID()
    });
    console.log('请求头验证:', Object.fromEntries(headers.entries()));
        if (!caseData.value?.features?.length) {
      throw new Error('无效的特征数据')
    }

    // 在发送请求前添加默认值
    const payload = {
      feature_vector: caseData.value.features || [], // 确保数组存在
      case_id: caseId
    }
    const response = await fetch('http://127.0.0.1:5000/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId
      },
      body: JSON.stringify(requestBody), // 直接使用requestBody，其包含feature_vector字段
      mode: 'cors',
      signal: controller.signal,
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`请求失败 (${response.status}): ${errorData.error || '未知错误'}`);
    }
    const abortTimer = setTimeout(() => controller.abort(), 10000);
    const { data } = await api.analyze(payload)
    if (!data?.features?.length) {
      throw new Error('API返回无效特征数据')
    }
    analysisResult.value = merge(
      {
        features: [],
        risk_scores: { high: 0, medium: 0, low: 0 },
        accuracy: 0
      },
      data
    )
    let rawRes = await response.text();
    rawRes = rawRes
      .replace(/^\uFEFF/, '') // 移除BOM头
      .replace(/[\x00-\x1F\x7F-\x9F]/g, '') // 移除控制字符
      .replace(/\n/g, '') // 移除换行符
      .trim();
    const isJSON = (str) => {
    try {
        JSON.parse(str);
        return true;
      } catch {
        return false;
      }
    };

    if (!isJSON(rawRes)) {
      console.error('Invalid JSON Response:', rawRes.slice(0, 200));
      throw new Error('服务器返回了非JSON格式数据');
    }
    const trimmedRes = rawRes.trim().replace(/\n/g, '');
    if (!/^\s*{.*}\s*$/.test(rawRes)) {
      console.error('原始响应格式异常:', {
        status: response.status,
        headers: [...response.headers],
        body: rawRes
      });
      throw new Error(`响应格式异常: ${trimmedRes.slice(0, 50)}`);
    }
    clearTimeout(abortTimer);

    if (!trimmedRes.startsWith('{') || !trimmedRes.endsWith('}')) {
      console.error('非法响应格式:', { rawRes, trimmedRes });
      throw new Error(`响应格式异常: ${trimmedRes.slice(0, 50)}`);
    }

    let result;
    try {
      result = JSON.parse(rawRes);
    } catch (parseError) {
      // 尝试修复常见JSON错误
      const repaired = rawRes
        .replace(/(['"])?([a-zA-Z0-9_]+)(['"])?:/g, '"$2":') // 修复键名引号
        .replace(/'/g, '"') // 替换单引号
        .replace(/,\s*([}\]])/g, '$1'); // 移除末尾逗号

      try {
        result = JSON.parse(repaired);
      } catch (retryError) {
        throw new Error(`数据解析失败: ${retryError.message}`);
      }
    }
    if (!response.ok) {
      const serverMessage = result.message || '未知服务器错误';
      throw new Error(`请求失败 (${response.status}): ${serverMessage}`);
    }
    // 第三步：可靠解析数据
    let validResult = result;
    if (!validResult) {
      try {
        validResult = JSON.parse(trimmedRes);
      } catch (parseError) {
        throw new Error(`JSON解析失败: ${parseError.message}\n原始内容: ${trimmedRes}`);
      }
    }
    console.debug('完整响应内容:', {
      raw: rawRes,
      trimmed: trimmedRes,
      parsed: validResult
    });


    if (!rawRes.startsWith('{') || !rawRes.endsWith('}')) {
      throw new Error(`响应格式异常: ${rawRes.slice(0, 50)}...`);
    }
    const featuresData = (result.features || []).map((item, index) => ({
      name: item?.name || `特征${index + 1}`,
      importance: Number(item?.importance) || 0
    }));
    console.log('请求追踪:', {
      id: requestId,
      status: response.status,
      headers: Object.fromEntries(response.headers.entries()),
      rawResponse: rawRes
    });
    //     // 数据清洗函数

    const riskScores = {
      high: Math.max(0, Math.min(100, result.risk_scores?.high || 0)),
      low: Math.max(0, Math.min(100, result.risk_scores?.low || 0))
    };

    if (!response) return
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP错误 ${response.status}: ${errorText}`)
    }

    const sanitizeData = (data) => {
      return JSON.parse(JSON.stringify(data, (key, value) => {
        // 处理数值异常
        if (typeof value === 'number') {
          if (isNaN(value) || !isFinite(value)) return 0
          return Number(value.toFixed(4))
        }
        // 处理Unicode字符
        if (key === 'name' && typeof value === 'string') {
          return value.replace(/\\u([\dA-F]{4})/gi,
            (_, grp) => String.fromCharCode(parseInt(grp, 16)))
        }
        return value
      }))
    }
  // Unicode解码函数
    // Unicode解码函数
    const normalizedResult = {
      risk_level: result.risk_level || '--',
      accuracy: Number(result.accuracy) || 0,
      suggested_treatment: result.suggested_treatment || '--',
      features: (result.features || []).map(f => ({
        name: f.name || `特征${f.index}`,
        importance: Number(f.importance) || 0
      })),
      risk_scores: {
        high: Math.max(0, Number(result.risk_scores?.high) || 0),
        low: Math.max(0, Number(result.risk_scores?.low) || 0)
      }
    };

    const mapFeatures = (features) => {
    if (!Array.isArray(features)) return [];
    if (!Array.isArray(features)) {
      console.error('无效的特征数据格式')
      return []
    }
    if (!Array.isArray(features)) {
        console.warn('无效特征输入，返回空数组');
        return [];
      }

    return features.map((f, index) => {
          const safeFeature = {
      code: String(f?.code || `feature_${index}`),
      name: String(f?.name || `特征${index + 1}`),
      importance: Math.min(1, Math.max(0, Number(f?.importance) || 0)),
      category: '未分类'
    };

    // 模糊匹配逻辑优化
    const matchedCode = Object.keys(medicalFeatures.feature_mappings)
      .find(k => k.toLowerCase() === safeFeature.code.toLowerCase());

    if (matchedCode) {
      const meta = medicalFeatures.feature_mappings[matchedCode];
      return {
        ...safeFeature,
        name: meta.name || safeFeature.name,
        category: meta.category || safeFeature.category,
        unit: meta.unit ? `${meta.unit}（${meta.reference}）` : '--'
      };
    }

    return safeFeature;
    // 从配置中查找匹配项（新增模糊匹配）
      const matchedFeature = Object.entries(medicalFeatures.feature_mappings).find(
        ([key, config]) =>
          key === f.code || // 精确匹配
          config.name.includes(f.displayName) // 名称模糊匹配
      );

      const meta = matchedFeature ? matchedFeature[1] : {};
      const fallbackName = `特征${index + 1}`;

      return {
        code: f.code || `feature_${index}`,
        displayName: meta.name || fallbackName,
        category: meta.category || '未分类',
        unit: meta.unit ? `${meta.unit}（${meta.reference}）` : '--',
        importance: parseFloat(f.importance) || 0,
        _raw: f
      };
    });
};
    const analysisData = {
      caseId: row.id,
      caseData: row,
      analysisResult: {
        risk_level: result.risk_level || 'unknown',
        accuracy: Math.max(0, Math.min(100, result.accuracy || 0)),
        suggested_treatment: result.suggested_treatment || '--',
        features: mapFeatures(result.features || []),  // ✅ 关键修改点
        risk_scores: {
          high: Math.max(0, Number(result.risk_scores?.high) || 0),
          medium: Math.max(0, Number(result.risk_scores?.medium) || 0),
          low: Math.max(0, Number(result.risk_scores?.low) || 0)
        }
      }
    };
    medicalFeatures.index_mappings = Object.entries(medicalFeatures.index_mappings).reduce(
      (acc, [key, value]) => {
        acc[String(key)] = String(value)
        return acc
      }, {}
    )
    const validateAnalysisData = (data) => {
      const requiredKeys = [
        'caseId',
        'analysisResult.risk_level',
        'analysisResult.accuracy'
      ];

  return requiredKeys.every(key => {
    const keys = key.split('.');
    let value = data;
    for (const k of keys) {
      if (!value.hasOwnProperty(k)) return false;
      value = value[k];
    }
    return true;
  });
};
    if (process.env.NODE_ENV === 'development') {
      console.log('当前特征配置:', {
        index_mappings: Object.keys(medicalFeatures.index_mappings),
        sample_mapping: Object.entries(medicalFeatures.index_mappings).slice(0, 3)
      });

      // 验证特征生成结果
      const testFeatures = generateFeatures("头痛", "偏头痛");
      console.assert(testFeatures.length === 132,
        `特征数组长度应为132，实际为${testFeatures.length}`);
    }
        // 保存到本地存储
    if (validateAnalysisData(analysisData)) {
      localStorage.setItem('lastAnalysisResult', JSON.stringify(analysisData));
    } else {
      console.error('无效的分析数据格式', analysisData);
      ElMessage.error('分析数据格式错误');
    }
    console.log('保存到localStorage的数据:', analysisData)
    localStorage.setItem('lastAnalysisResult', JSON.stringify(analysisData));
    // 导航到可视化页面

    router.push({
      path: '/prediction_result',
      query: {
        caseId: row.id,
        timestamp: Date.now() // 防止路由缓存
      }
    })
    // ...后续处理保持不变...
  } catch (error) {
    if (error.response) {
      console.error('完整错误响应:', {
        status: error.response.status,
        headers: error.response.headers,
        data: await error.response.text()
      });
    }
    console.error('病例分析失败详情:', {
      病例ID: row?.id,
      主诉: String(row?.complaint).slice(0, 50),
      诊断: String(row?.diagnosis).slice(0, 50),
      特征数组类型: Array.isArray(row?.features) ? 'array' : typeof row?.features,
      特征长度: row?.features?.length || 0,
      错误信息: error.message
    });
    console.error('完整错误信息:', {
        url: 'http://127.0.0.1:5000/predict',
        requestBody: requestBody ? { // 添加安全判断
            featureLength: requestBody.features.length,
            nonZeroCount: requestBody.features.filter(v => v === 1).length
        } : 'undefined',
        error: error.message
    });
      ElMessage.error(`分析失败: ${error.message}`);
    if (error.name === 'AbortError') {
      ElMessage.warning('请求超时，请重试');
    } else {
      console.error('完整错误追踪:', {
        requestId,
        error: error.stack
      });
      ElMessage.error(`分析失败: ${error.message}`);
    }
    console.error('特征预处理失败:', e);
    features = new Array(132).fill(0);
  } finally {
    clearTimeout(timeoutId);
    controller.abort();
  }
};

const decodeUnicode = (str) => {
  return str.replace(/\\u([\dA-F]{4})/gi,
    (match, grp) => String.fromCharCode(parseInt(grp, 16))) // 补全括号
}

</script>

<style scoped>
.chart-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}
.el-table-column--operation .el-button {
  margin-left: 0;
}
.main-container {
  display: flex;
  min-height: 100vh;
}
.cropper-container {
  width: 100%;
  height: 400px;
  background: #f0f2f5;
}

/* 修复图片元素样式 */
.cropper-container img {
  display: block;
  max-width: 100%;
  max-height: 100%;
  margin: 0 auto;
  width: 100%; /* 添加冒号和值 */
}
.sidebar-menu {
  width: 200px;
  border-right: 1px solid #e6e6e6;
}

.main-content {
  flex: 1;
}

.el-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}
.analysis-container {
  width: 100%;
  height: 600px;
  position: relative;
}
.el-skeleton {
  position: absolute;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.9);
  z-index: 10;
}
.user-panel {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-panel:hover {
  background: #f5f7fa;
}

.username {
  font-weight: 500;
  color: #606266;
}
.cropper-container {
  width: 100%;
  height: 400px;
  overflow: hidden;
}

.case-list {
  margin-top: 20px;
  width: 90%;
  margin-left: auto;
  margin-right: auto;
}

.scroll-container {
  max-height: 60vh;
  overflow-y: auto;
  position: relative;
}

/* 优化滚动条样式 */

.scroll-container::-webkit-scrollbar {
  width: 8px;
}
.scroll-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.patient-info-group {
  display: flex;
  gap: 10px;
  align-items: center;
}
</style>
