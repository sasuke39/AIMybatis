import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import os

class MapperGenerator:
    def __init__(self, base_model_name="facebook/opt-350m", checkpoint_path="./mybatis_mapper_generator"):
        """
        初始化生成器
        :param base_model_name: 基础模型名称
        :param checkpoint_path: 训练后的检查点路径
        """
        # 设置环境变量
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            use_fast=True  # 使用快速分词器
        )
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float32,
            device_map="auto",
            low_cpu_mem_usage=True,  # 减少CPU内存使用
        )
        self.model = PeftModel.from_pretrained(base_model, checkpoint_path)
        self.model.eval()  # 设置为评估模式
        
        # 预热模型
        self._warmup()
        
    def _warmup(self):
        """预热模型，第一次推理通常较慢"""
        dummy_input = "public class Test {}"
        _ = self.generate_mapper(dummy_input)

    def generate_mapper(self, entity_content: str, package_info: dict = None) -> str:
        """
        为给定的实体类生成Mapper XML
        :param entity_content: 实体类的内容
        :param package_info: 包信息（可选）
        :return: 生成的Mapper XML内容
        """
        # 构建输入提示
        prompt = f"""请根据以下Java实体类生成对应的MyBatis Mapper XML文件。

Java实体类:
{entity_content}

生成的Mapper XML应该包含:
1. 基本的CRUD操作
2. ResultMap映射
3. 正确的namespace
4. 所有字段的映射

Mapper XML:
"""
        
        # 如果提供了包信息，添加到提示中
        if package_info:
            package_context = f"""包信息:
实体类包名: {package_info.get('entity_package', '')}
Mapper包名: {package_info.get('mapper_package', '')}

"""
            prompt = package_context + prompt

        # 生成输出
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model.generate(
            input_ids=inputs["input_ids"].to(self.model.device),
            max_new_tokens=1024,  # 只使用 max_new_tokens
            num_beams=5,  # 使用束搜索
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            early_stopping=True  # 现在可以使用 early_stopping，因为我们设置了 num_beams > 1
        )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 提取XML部分
        try:
            xml_start = generated_text.index('<?xml')
            return generated_text[xml_start:]
        except ValueError:
            # 如果没有找到XML标记，返回整个生成的文本
            return generated_text

    def generate_mapper_for_file(self, java_file_path: str, output_dir: str = "./generated_mappers"):
        """
        为指定的Java文件生成Mapper XML
        :param java_file_path: Java文件路径
        :param output_dir: 输出目录
        """
        # 读取Java文件
        with open(java_file_path, 'r', encoding='utf-8') as f:
            entity_content = f.read()

        # 生成Mapper内容
        mapper_content = self.generate_mapper(entity_content)

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 生成输出文件名
        file_name = os.path.basename(java_file_path)
        output_file = os.path.join(output_dir, file_name.replace('.java', 'Mapper.xml'))

        # 保存生成的Mapper
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(mapper_content)

        return output_file 