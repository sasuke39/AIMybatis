import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import os

class InteractiveMapperGenerator:
    def __init__(self, base_model_name="facebook/opt-350m", checkpoint_path="./mybatis_mapper_generator"):
        """初始化生成器并预热"""
        print("正在加载模型...")
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
        self.tokenizer = AutoTokenizer.from_pretrained(
            base_model_name,
            use_fast=True
        )
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float32,
            device_map="auto",
            low_cpu_mem_usage=True,
        )
        self.model = PeftModel.from_pretrained(base_model, checkpoint_path)
        self.model.eval()
        
        print("模型加载完成，正在预热...")
        self._warmup()
        print("预热完成，可以开始生成了！")

    def _warmup(self):
        """预热模型"""
        dummy_input = "public class Test {}"
        _ = self.generate_mapper(dummy_input)

    def generate_mapper(self, entity_content: str) -> str:
        """生成Mapper XML"""
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
        
        with torch.no_grad():
            inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
            outputs = self.model.generate(
                input_ids=inputs["input_ids"].to(self.model.device),
                max_new_tokens=1024,
                num_beams=5,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.2,
                no_repeat_ngram_size=3,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                early_stopping=True
            )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        try:
            xml_start = generated_text.index('<?xml')
            return generated_text[xml_start:]
        except ValueError:
            return generated_text

    def interactive_session(self):
        """交互式生成会话"""
        print("\n=== MyBatis Mapper 交互式生成器 ===")
        print("请输入Java实体类代码 (输入 'exit' 结束，输入 'done' 完成当前输入)")
        
        while True:
            print("\n等待输入...")
            lines = []
            while True:
                try:
                    line = input()
                    if line.lower() == 'exit':
                        print("结束会话")
                        return
                    if line.lower() == 'done':
                        break
                    lines.append(line)
                except KeyboardInterrupt:
                    print("\n检测到Ctrl+C，结束会话")
                    return
                except EOFError:
                    print("\n检测到EOF，结束会话")
                    return
            
            if not lines:
                continue
                
            entity_content = '\n'.join(lines)
            
            try:
                print("\n正在生成Mapper XML...")
                mapper_xml = self.generate_mapper(entity_content)
                print("\n生成的Mapper XML:")
                print("=" * 50)
                print(mapper_xml)
                print("=" * 50)
                
                save = input("\n是否保存到文件? (y/n): ")
                if save.lower() == 'y':
                    file_name = input("请输入保存的文件名 (不包含.xml): ") or "GeneratedMapper"
                    output_dir = "./generated_mappers"
                    file_path = f"{output_dir}/{file_name}.xml"
                    
                    os.makedirs(output_dir, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(mapper_xml)
                    print(f"已保存到: {file_path}")
            
            except Exception as e:
                print(f"生成过程中出现错误: {str(e)}")

def main():
    generator = InteractiveMapperGenerator()
    generator.interactive_session()

if __name__ == "__main__":
    main() 