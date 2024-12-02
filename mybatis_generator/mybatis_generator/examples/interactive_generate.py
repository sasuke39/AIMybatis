from ...mybatis_generator.inference import MapperGenerator

def generate_interactive():
    print("=== Mybatis Mapper 生成器 ===")
    print("请输入Java实体类代码 (输入 'exit' 结束，输入 'done' 完成输入):")
    
    # 初始化生成器
    generator = MapperGenerator(
        base_model_name="facebook/opt-350m",
        checkpoint_path="./mybatis_mapper_generator"  # 确保这是你训练后的模型路径
    )
    
    while True:
        # 收集多行输入
        lines = []
        while True:
            line = input()
            if line.lower() == 'exit':
                return
            if line.lower() == 'done':
                break
            lines.append(line)
        
        if not lines:
            continue
            
        # 合并输入的代码
        entity_content = '\n'.join(lines)
        
        try:
            # 生成Mapper
            print("\n生成的Mapper XML:")
            print("=" * 50)
            mapper_xml = generator.generate_mapper(entity_content)
            print(mapper_xml)
            print("=" * 50)
            
            # 询问是否保存
            save = input("\n是否保存到文件? (y/n): ")
            if save.lower() == 'y':
                file_name = input("请输入保存的文件名 (不包含.xml): ") or "GeneratedMapper"
                output_dir = "./generated_mappers"
                file_path = f"{output_dir}/{file_name}.xml"
                
                import os
                os.makedirs(output_dir, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(mapper_xml)
                print(f"已保存到: {file_path}")
        
        except Exception as e:
            print(f"生成过程中出现错误: {str(e)}")
        
        print("\n请输入下一个实体类代码 (输入 'exit' 结束，输入 'done' 完成输入):")

if __name__ == "__main__":
    generate_interactive() 