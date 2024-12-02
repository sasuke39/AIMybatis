import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mybatis_generator.inference import MapperGenerator

# 初始化生成器
generator = MapperGenerator()

# 方式1：直接从字符串生成
entity_content = """
package com.example.entity;

public class User {
    private Long id;
    private String username;
    private String email;
}
"""

# 生成Mapper XML
mapper_xml = generator.generate_mapper(entity_content)
print(mapper_xml) 