import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import numpy as np


def load_data(path):
    """加载数据并删除未命名列"""
    df = pd.read_csv(path)
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

def preprocess_data(df):
    """数据预处理"""
    df.columns = df.columns.str.strip().str.replace(' ', '')
    df['prognosis'] = df['prognosis'].str.strip()
    df['prognosis'] = df['prognosis'].replace(
        'Peptic ulcer diseae',
        'Peptic ulcer disease'
    )
    return df

disease_mapping = {
    'AIDS': '艾滋病',
    'Acne': '痤疮',
    'Alcoholic hepatitis': '酒精性肝炎',
    'Allergy': '过敏',
    'Arthritis': '关节炎',
    'Bronchial Asthma': '支气管哮喘',
    'Cervical spondylosis': '颈椎病',
    'Chicken pox': '水痘',
    'Chronic cholestasis': '慢性胆汁淤积',
    'Common Cold': '普通感冒',
    'Dengue': '登革热',
    'Diabetes': '糖尿病',
    'Dimorphic hemorrhoids': '混合痔',
    'Drug Reaction': '药物反应',
    'Fungal infection': '真菌感染',
    'GERD': '胃食管反流病',
    'Gastroenteritis': '胃肠炎',
    'Heart attack': '心脏病发作',
    'Hepatitis B': '乙型肝炎',
    'Hepatitis C': '丙型肝炎',
    'Hepatitis D': '丁型肝炎',
    'Hepatitis E': '戊型肝炎',
    'Hypertension': '高血压',
    'Hyperthyroidism': '甲状腺功能亢进',
    'Hypoglycemia': '低血糖',
    'Hypothyroidism': '甲状腺功能减退',
    'Impetigo': '脓疱病',
    'Jaundice': '黄疸',
    'Malaria': '疟疾',
    'Migraine': '偏头痛',
    'Osteoarthristis': '骨关节炎',
    'Paralysis (brain hemorrhage)': '瘫痪（脑出血）',
    'Peptic ulcer disease': '消化性溃疡',
    'Pneumonia': '肺炎',
    'Psoriasis': '银屑病',
    'Tuberculosis': '肺结核',
    'Typhoid': '伤寒',
    'Urinary tract infection': '尿路感染',
    'Varicose veins': '静脉曲张',
    'hepatitis A': '甲型肝炎'
}

# 修改预测输出部分
def translate_disease(en_name, mapping):
    """安全获取中文病名，缺失时返回英文"""
    return mapping.get(en_name, en_name)
# 加载并预处理数据
train_df = preprocess_data(load_data("../static/Training.csv"))
test_df = preprocess_data(load_data("../static/Testing.csv"))

# 确保特征一致性
common_features = list(
    set(train_df.columns)
    & set(test_df.columns)
    - {'prognosis'}
)

# 准备数据
X_train = train_df[common_features]
y_train = train_df['prognosis']
X_test = test_df[common_features]
y_test = test_df['prognosis']

# 初始化模型
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42
)

# 训练与评估
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
print(f"测试集准确率: {accuracy_score(y_test, y_pred):.2f}")

# 示例预测
sample_case = X_test.iloc[0:9]

# 在评估后添加完整测试集翻译
print("\n测试集详细结果:")
for en_name, pred in zip(y_test, y_pred):
    zh_actual = translate_disease(en_name, disease_mapping)
    zh_pred = translate_disease(pred, disease_mapping)
    print(f"实际: {zh_actual:<10} | 预测: {zh_pred}")

# 修改示例预测输出
sample_case = X_test.iloc[0:1]
pred_en = model.predict(sample_case)[0]
actual_en = y_test.iloc[0]

np.save('feature_means.npy', X_train.mean(axis=0))
np.save('feature_stds.npy', X_train.std(axis=0))
joblib.dump(model, 'medic_predict_model.pkl')
print(f"\n示例病例预测:")
print(f"预测疾病: {translate_disease(pred_en, disease_mapping)}")
print(f"实际诊断: {translate_disease(actual_en, disease_mapping)}")