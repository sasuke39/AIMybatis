from core.code_analyzer import ProjectAnalyzer
from typing import List, Dict
from torch.optim.lr_scheduler import CosineAnnealingLR  # 余弦退火
from torch.optim.lr_scheduler import OneCycleLR  # 单周期学习率

class TrainingDataGenerator:
    def __init__(self, mapper_dir: str, entity_dir: str, mapper_java_dir: str):
        self.analyzer = ProjectAnalyzer(mapper_dir, entity_dir, mapper_java_dir)
        
    def generate_training_data(self) -> List[Dict]:
        """生成训练数据"""
        # 分析项目
        self.analyzer.analyze()
        
        # 获取训练对
        training_pairs = self.analyzer.get_training_pairs()
        
        # 转换为训练数据格式
        training_data = []
        
        # 为每个实体类生成多个不同功能的训练样本
        for pair in training_pairs:
            entity = pair['entity']
            entity_name = entity['name']
            table_name = self._get_table_name(entity_name)
            fields = entity['fields']
            
            print(f"\n=== 正在处理实体类: {entity_name} ===")
            
            # 生成不同类型的操作样本
            samples = self._generate_operation_samples(entity_name, table_name, fields)
            
            for sample in samples:
                print("\n--- 训练样本 ---")
                print("Input:")
                print(sample['description'])
                print("\nOutput:")
                print(sample['xml'])
                print("-------------")

                training_data.append({
                    "instruction": "根据input的内容解析出其中的实体类名，和需要的功能，再通过功能生成对应的Mybatis Mapper XML",
                    "input": sample['description'],
                    "output": sample['xml'],
                    "project_context": {
                        "entity_name": entity_name,
                        "table_name": table_name,
                        "fields": fields
                    }
                })
        
        print(f"\n总共生成了 {len(training_data)} 个训练样本")
        return training_data
    
    def _get_table_name(self, entity_name: str) -> str:
        """从实体类名生成表名"""
        # User -> t_user, UserOrder -> t_user_order
        name = ''.join(['_' + c.lower() if c.isupper() else c for c in entity_name]).lstrip('_')
        return f"t_{name}"
    
    def _generate_operation_samples(self, entity_name: str, table_name: str, fields: List[Dict]) -> List[Dict]:
        """生成不同类型的操作样本"""
        samples = []
        
        # 遍历字段生成更新操作
        for field in fields:
            field_name = field['name']
            column_name = self._to_snake_case(field_name)
            
            # 生成更新状态的样本
            if field_name.lower().endswith('status'):
                samples.append({
                    "description": f"生成根据id更新{entity_name}的{field_name}的sql",
                    "xml": f"""    <update id="update{field_name.capitalize()}ById">
        UPDATE `{table_name}`
        SET {column_name} = #{{{field_name}}},
            update_time = now()
        WHERE id = #{id}
    </update>"""
                })
            
            # 生成批量更新的样本
            samples.append({
                "description": f"生成批量更新{entity_name}的{field_name}的sql",
                "xml": f"""    <update id="batchUpdate{field_name.capitalize()}">
        UPDATE `{table_name}`
        SET {column_name} = #{{{field_name}}},
            update_time = now()
        WHERE id IN
        <foreach collection="ids" item="id" open="(" separator="," close=")">
            #{id}
        </foreach>
    </update>"""
            })
        
        # 生成查询样本
        samples.append({
            "description": f"生成根据id查询{entity_name}详情的sql",
            "xml": f"""    <select id="selectById" resultMap="BaseResultMap">
        SELECT <include refid="Base_Column_List"/>
        FROM `{table_name}`
        WHERE id = #{id}
    </select>"""
        })
        
        # 生成列表查询样本
        samples.append({
            "description": f"生成查询{entity_name}列表的sql，支持多个字段查询条件",
            "xml": f"""    <select id="selectList" resultMap="BaseResultMap">
        SELECT <include refid="Base_Column_List"/>
        FROM `{table_name}`
        <where>
            <if test="id != null">
                AND id = #{id}
            </if>
            {''.join([f'''
            <if test="{field['name']} != null">
                AND {self._to_snake_case(field['name'])} = #{{{field['name']}}}
            </if>''' for field in fields])}
        </where>
    </select>"""
        })
        
        return samples
    
    def _to_snake_case(self, name: str) -> str:
        """驼峰命名转下划线命名"""
        return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')
    
    def _format_entity_class(self, entity_info: Dict) -> str:
        """格式化实体类信息"""
        with open(entity_info['file_path'], 'r', encoding='utf-8') as f:
            return f.read()
    
    def _get_package_structure(self, entity_info: Dict) -> Dict:
        """获取包结构信息"""
        return {
            'entity_package': entity_info['package'],
            'mapper_package': f"{entity_info['package'].replace('.entity', '.mapper')}"
        }