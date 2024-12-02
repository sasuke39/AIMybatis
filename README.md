# MyBatis Mapper Generator

基于大语言模型的智能 MyBatis Mapper 生成器，可以通过自然语言描述生成对应的 Mapper XML 文件。

## 🌟 特性

- 🤖 基于大语言模型的智能生成
- 💡 支持自然语言描述需求
- 🛠 自动处理命名转换（驼峰转下划线）
- 📝 生成标准的 MyBatis Mapper XML
- 🔄 支持批量生成和交互式生成
- 🎯 支持多种数据库操作（CRUD）

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PyTorch 2.0+
- transformers
- peft
- trl

### 安装

```bash
# 克隆项目
git clone https://github.com/your-project/mybatis-mapper-generator.git
cd mybatis-mapper-generator

# 安装依赖
pip install -e .
```

### 使用方法

1. **交互式生成**

```bash
python -m mybatis_generator.interactive_mapper
```

2. **批量生成**

```python
from mybatis_generator.inference import MapperGenerator

generator = MapperGenerator()
generator.generate_mapper_for_file("path/to/entity.java")
```

## 📖 使用示例

### 1. 自然语言描述生成 Mapper
```
输入: 生成根据id更新User的status的sql

输出:
<update id="updateStatusById">
    UPDATE `t_user`
    SET status = #{status},
        update_time = now()
    WHERE id = #{id}
</update>
```

### 2. 批量处理实体类

```python
from mybatis_generator.inference import MapperGenerator

generator = MapperGenerator()

# 处理单个文件
generator.generate_mapper_for_file("User.java")

# 批量处理目录
import glob
entity_files = glob.glob("./entities/*.java")
for file in entity_files:
    generator.generate_mapper_for_file(file)
```

## 🛠 项目结构

```
mybatis_generator/
├── mybatis_generator/
│   ├── core/
│   │   ├── code_analyzer.py        # 代码分析器
│   │   └── training_data_generator.py  # 训练数据生成
│   ├── data/
│   │   └── dataset_example.json    # 示例数据
│   ├── examples/
│   │   └── generate_mapper.py      # 使用示例
│   ├── train.py                    # 训练脚本
│   ├── inference.py                # 推理模块
│   └── interactive_mapper.py       # 交互式生成器
└── tests/
    └── __init__.py
```

## 🔄 训练流程

### 1. 准备训练数据

```python
from mybatis_generator.core.training_data_generator import TrainingDataGenerator

data_generator = TrainingDataGenerator(
    mapper_dir="/path/to/mapper/xml",
    entity_dir="/path/to/entity/classes",
    mapper_java_dir="/path/to/mapper/java"
)
```

### 2. 训练参数配置

```python
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-4,
    warmup_steps=100,
    # ... 更多参数配置
)
```

### 3. 开始训练

```bash
python -m mybatis_generator.train
```

## ⚙️ 配置说明

### 模型配置
- `model_name`: 基础模型名称 (默认: "facebook/opt-350m")
- `max_seq_length`: 最大序列长度 (默认: 512)
- `device`: 训练设备 (自动选择)

### 训练配置
- `num_epochs`: 训练轮数
- `batch_size`: 批处理大小
- `learning_rate`: 学习率
- `warmup_steps`: 预热步数
- `weight_decay`: 权重衰减

## 📝 注意事项

1. 确保实体类和 Mapper 文件的命名符合规范
2. 训练数据质量直接影响生成结果
3. 建议使用 GPU 进行训练
4. 定期保存训练检查点

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Hugging Face Transformers](https://github.com/huggingface/transformers)
- [PEFT](https://github.com/huggingface/peft)
- [TRL](https://github.com/huggingface/trl)

## 📧 联系方式

- 项目维护者: [xian hong]
- Email: [1255606156@example.com]
```


