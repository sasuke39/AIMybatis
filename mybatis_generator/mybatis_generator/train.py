import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from datasets import Dataset, DatasetDict
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
from core.training_data_generator import TrainingDataGenerator
import random

# 限制PyTorch使用的线程数
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# 1. 生成训练数据
data_generator = TrainingDataGenerator(
    mapper_dir="/Users/haochidebingqilinkaobulei/IdeaProjects/finance/finance-core/finance-core-dao/src/main/resources",
    entity_dir="/Users/haochidebingqilinkaobulei/IdeaProjects/finance/finance-core/finance-core-dao/src/main/java/com/yangt/finance/core/db/entity",
    mapper_java_dir="/Users/haochidebingqilinkaobulei/IdeaProjects/finance/finance-core/finance-core-dao/src/main/java/com/yangt/finance/core/db/mapper"
)
training_data = data_generator.generate_training_data()

# 2. 准备提示模板
PROMPT_TEMPLATE = """
### 项目上下文
实体类: {entity_name}
表名: {table_name}

### 指令: {instruction}

### 输入: 
{input}

### 输出:
{output}
"""

def load_training_data(training_data):
    formatted_data = []
    for item in training_data:
        context = item['project_context']
        input_text = PROMPT_TEMPLATE.format(
            entity_name=context['entity_name'],
            table_name=context['table_name'],
            instruction=item['instruction'],
            input=item['input'],
            output=""
        )
        formatted_data.append({
            "input_text": input_text,
            "output_text": item['output']
        })
    return formatted_data

# 3. 准备模型和分词器
model_name = "facebook/opt-350m"

tokenizer = AutoTokenizer.from_pretrained(
    model_name,
    trust_remote_code=True,
    padding_side="right",
    model_max_length=512
)
# 确保有pad token
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,
    device_map="auto",
    trust_remote_code=True
)
model.config.pad_token_id = tokenizer.pad_token_id

# 4. 准备数据集
train_data = load_training_data(training_data)

# 划分训练集和验证集
random.shuffle(train_data)
split_point = int(len(train_data) * 0.9)

def format_dataset(examples):
    """格式化数据集"""
    texts = examples["input_text"]
    targets = examples["output_text"]
    
    # 对输入文本进行编码
    inputs = tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )
    
    # 对目标文本进行编码
    labels = tokenizer(
        targets,
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )
    
    return {
        "input_ids": inputs["input_ids"],
        "attention_mask": inputs["attention_mask"],
        "labels": labels["input_ids"]
    }

# 创建和格式化数据集
train_dataset = Dataset.from_list(train_data[:split_point]).map(
    format_dataset,
    batched=True,
    remove_columns=["input_text", "output_text"]
)
eval_dataset = Dataset.from_list(train_data[split_point:]).map(
    format_dataset,
    batched=True,
    remove_columns=["input_text", "output_text"]
)

# 5. LoRA配置
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)

# 6. 应用LoRA
model = get_peft_model(model, lora_config)

# 7. 训练参数
num_epochs = 3
total_steps = len(train_dataset) * num_epochs
warmup_steps = total_steps // 10

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=num_epochs,
    per_device_train_batch_size=4,
    per_device_eval_batch_size=4,
    gradient_accumulation_steps=4,
    
    # 学习率调度
    learning_rate=2e-4,
    warmup_steps=warmup_steps,
    lr_scheduler_type="cosine_with_restarts",
    
    # 梯度裁剪和权重衰减
    max_grad_norm=1.0,
    weight_decay=0.01,
    
    # 评估和保存
    save_strategy="steps",
    save_steps=100,
    evaluation_strategy="steps",
    eval_steps=100,
    
    # 日志
    logging_dir="./logs",
    logging_steps=10,
    
    # 其他优化
    fp16=False,
    optim="adamw_torch",
    adam_beta1=0.9,
    adam_beta2=0.999,
    adam_epsilon=1e-8,
    
    # 早停策略
    load_best_model_at_end=True,
    metric_for_best_model="loss",
    greater_is_better=False,
    
    # 移除评估策略，因为我们现在提供验证集
    remove_unused_columns=False,  # 防止删除必要的列
)

# 8. 训练器
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    tokenizer=tokenizer,
    max_seq_length=512,
)

# 9. 开始训练
trainer.train()

# 10. 保存模型
trainer.save_model("./mybatis_mapper_generator")