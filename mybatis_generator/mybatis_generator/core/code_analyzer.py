import os
import javalang
from typing import List, Dict
from xml.etree import ElementTree as ET

class ProjectAnalyzer:
    def __init__(self, mapper_dir: str, entity_dir: str, mapper_java_dir: str):
        """
        初始化项目分析器
        :param mapper_dir: Mapper XML文件所在目录
        :param entity_dir: 实体类所在目录
        :param mapper_java_dir: Mapper接口文件所在目录
        """
        self.mapper_dir = mapper_dir
        self.entity_dir = entity_dir
        self.mapper_java_dir = mapper_java_dir
        self.entity_classes = {}
        self.existing_mappers = {}
        self.mapper_interfaces = {}
        self.naming_patterns = {}  # 添加命名模式字典
        
        print("\n=== 初始化项目分析器 ===")
        print(f"Mapper XML目录: {mapper_dir}")
        print(f"实体类目录: {entity_dir}")
        print(f"Mapper接口目录: {mapper_java_dir}")
        
        # 检查目录是否存在
        self._check_directories()
        
    def _check_directories(self):
        """检查必要的目录是否存在"""
        for dir_path, dir_name in [
            (self.mapper_dir, "Mapper XML"),
            (self.entity_dir, "实体类"),
            (self.mapper_java_dir, "Mapper接口")
        ]:
            if not os.path.exists(dir_path):
                print(f"警告: {dir_name}目录不存在: {dir_path}")
            else:
                # 列出目录中的文件
                files = os.listdir(dir_path)
                print(f"\n{dir_name}目录中的文件:")
                for file in files:
                    print(f"- {file}")
        
    def analyze(self):
        """分析项目结构"""
        print("\n=== 开始项目分析 ===")
        self._scan_mapper_interfaces()
        self._scan_mappers()
        self._scan_entities()
        self._analyze_naming_patterns()  # 添加命名模式分析
        self._match_mapper_info()
        
    def _analyze_naming_patterns(self):
        """分析项目的命名模式"""
        self.naming_patterns = {
            'entity_suffix': self._detect_entity_suffix(),
            'table_prefix': self._detect_table_prefix(),
            'column_style': self._detect_column_style()
        }
        
    def _detect_entity_suffix(self) -> str:
        """检测实体类的后缀模式"""
        suffixes = {'DO': 0, 'Entity': 0, 'Model': 0, '': 0}
        for class_name in self.entity_classes.keys():
            name = class_name.split('.')[-1]
            for suffix in suffixes.keys():
                if name.endswith(suffix):
                    suffixes[suffix] += 1
                    break
        # 返回最常用的后缀
        return max(suffixes.items(), key=lambda x: x[1])[0]
        
    def _detect_table_prefix(self) -> str:
        """检测表名前缀模式"""
        # 从XML中分析表名前缀
        prefixes = {}
        for mapper in self.existing_mappers.values():
            content = mapper['content']
            # 简单的表名提取逻辑，实际项目中可能需要更复杂的解析
            table_names = self._extract_table_names(content)
            for table in table_names:
                prefix = table.split('_')[0] if '_' in table else ''
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
        return max(prefixes.items(), key=lambda x: x[1])[0] if prefixes else ''
        
    def _detect_column_style(self) -> str:
        """检测字段命名风格"""
        # 从XML中分析字段命名风格
        styles = {'camelCase': 0, 'snake_case': 0}
        for mapper in self.existing_mappers.values():
            content = mapper['content']
            if 'column=' in content:
                # 简单判断是否使用下划线
                if '_' in content:
                    styles['snake_case'] += 1
                else:
                    styles['camelCase'] += 1
        return max(styles.items(), key=lambda x: x[1])[0]
        
    def _extract_table_names(self, content: str) -> List[str]:
        """从SQL中提取表名"""
        tables = []
        # 简单的表名提取逻辑
        keywords = ['FROM', 'JOIN', 'UPDATE', 'INTO']
        for keyword in keywords:
            pos = content.find(keyword)
            if pos != -1:
                # 提取紧跟在关键字后面的表名
                # 这里的逻辑可能需要根据实际SQL复杂度调整
                table = content[pos:].split()[1].strip('`[]"')
                tables.append(table)
        return list(set(tables))  # 去重
        
    def _scan_mapper_interfaces(self):
        """扫描Mapper接口文件"""
        print("\n=== 扫描Mapper接口文件 ===")
        for root, _, files in os.walk(self.mapper_java_dir):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    print(f"\n发现Mapper接口文件: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print("文件内容预览:")
                            print(content[:200] + "..." if len(content) > 200 else content)
                        tree = javalang.parse.parse(content)
                        self._process_mapper_interface(tree, file_path)
                        print(f"当前已解析的接口数量: {len(self.mapper_interfaces)}")
                    except Exception as e:
                        print(f"解析出错: {str(e)}")

    def _process_mapper_interface(self, tree, file_path: str):
        """处理Mapper接口文件"""
        try:
            # 修改包名获取方式
            package = tree.package.name if tree.package else ''
            print(f"处理接口文件: {file_path}, 包名: {package}")
            
            for _, node in tree.filter(javalang.tree.InterfaceDeclaration):
                full_interface_name = f"{package}.{node.name}"
                methods = self._extract_mapper_methods(node)
                self.mapper_interfaces[full_interface_name] = {
                    'name': node.name,
                    'package': package,
                    'methods': methods,
                    'file_path': file_path
                }
                print(f"添加接口: {full_interface_name}")
        except Exception as e:
            print(f"处理Mapper接口文件出错 {file_path}: {str(e)}")

    def _extract_mapper_methods(self, node) -> List[Dict]:
        """提取Mapper接口中的方法信息"""
        methods = []
        for method in node.methods:
            method_info = {
                'name': method.name,
                'return_type': self._get_full_type(method.return_type),
                'parameters': self._extract_parameters(method.parameters),
                'annotations': self._extract_annotations(method.annotations),
                'documentation': self._extract_javadoc(method)
            }
            methods.append(method_info)
        return methods

    def _extract_javadoc(self, method) -> Dict:
        """提取方法的JavaDoc注释"""
        if hasattr(method, 'documentation'):
            doc = method.documentation
            return {
                'description': doc.description if doc else '',
                'params': {param.name: param.description for param in doc.params} if doc and doc.params else {},
                'return': doc.return_doc if doc and doc.return_doc else ''
            }
        return {}

    def _extract_annotations(self, annotations) -> List[Dict]:
        """提取注解信息"""
        result = []
        for ann in annotations:
            ann_info = {
                'name': ann.name,
                'elements': {}
            }
            if ann.element:
                for elem in ann.element:
                    if isinstance(elem, javalang.tree.ElementValuePair):
                        ann_info['elements'][elem.name] = elem.value.value
                    else:
                        ann_info['elements']['value'] = elem.value
            result.append(ann_info)
        return result

    def _match_mapper_info(self):
        """匹配Mapper接口和XML信息"""
        print("\n=== 匹配结果统计 ===")
        print(f"找到的实体类数量: {len(self.entity_classes)}")
        print(f"找到的Mapper XML数量: {len(self.existing_mappers)}")
        print(f"找到的Mapper接口数量: {len(self.mapper_interfaces)}")
        
        print("\n实体类列表:")
        for class_name in self.entity_classes:
            print(f"- {class_name}")
            
        print("\nMapper XML列表:")
        for namespace in self.existing_mappers:
            print(f"- {namespace}")
            
        print("\nMapper接口列表:")
        for interface_name in self.mapper_interfaces:
            print(f"- {interface_name}")

    def _scan_mappers(self):
        """扫描所有Mapper XML文件"""
        print("\n=== 扫描Mapper XML文件 ===")
        for root, _, files in os.walk(self.mapper_dir):
            for file in files:
                if file.endswith('.xml'):
                    file_path = os.path.join(root, file)
                    print(f"\n发现Mapper XML文件: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print("文件内容预览:")
                            print(content[:200] + "..." if len(content) > 200 else content)
                        mapper_info = self._parse_mapper_file(file_path)
                        if mapper_info:
                            self.existing_mappers[mapper_info['namespace']] = mapper_info
                            print(f"解析结果:")
                            print(f"- namespace: {mapper_info['namespace']}")
                            print(f"- entity_type: {mapper_info['entity_type']}")
                    except Exception as e:
                        print(f"解析出错: {str(e)}")

    def _parse_mapper_file(self, file_path: str) -> Dict:
        """解析Mapper XML文件"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            namespace = root.get('namespace')
            
            # 提取实体类型（从resultMap或参数类型中）
            entity_type = self._extract_entity_type(root)
            
            return {
                'file_path': file_path,
                'namespace': namespace,
                'entity_type': entity_type,
                'content': ET.tostring(root, encoding='utf-8').decode('utf-8')
            }
        except Exception as e:
            print(f"解析XML文件失败 {file_path}: {str(e)}")
            return None

    def _scan_entities(self):
        """扫描实体类文件"""
        print("\n=== 扫描实体类文件 ===")
        for root, _, files in os.walk(self.entity_dir):
            for file in files:
                if file.endswith('.java'):
                    file_path = os.path.join(root, file)
                    print(f"\n发现实体类文件: {file_path}")
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            print("文件内容预览:")
                            print(content[:200] + "..." if len(content) > 200 else content)
                        tree = javalang.parse.parse(content)
                        self._process_java_file(tree, file_path)
                    except Exception as e:
                        print(f"解析出错: {str(e)}")

    def _process_java_file(self, tree, file_path: str):
        """处理Java文件"""
        try:
            # 修改包名获取方式
            package = tree.package.name if tree.package else ''
            if not package:
                # 如果没有包声明，使用目录结构作为包名
                rel_path = os.path.relpath(os.path.dirname(file_path), self.entity_dir)
                package = rel_path.replace(os.sep, '.')
            
            # 获取所有类声明
            for _, node in tree.filter(javalang.tree.ClassDeclaration):
                full_class_name = f"{package}.{node.name}"
                self.entity_classes[full_class_name] = {
                    'name': node.name,
                    'package': package,
                    'fields': self._extract_fields(node),
                    'file_path': file_path
                }
        except Exception as e:
            print(f"处理Java文件出错 {file_path}: {str(e)}")

    def _extract_fields(self, node) -> List[Dict]:
        """提取类的字段信息"""
        fields = []
        for field in node.fields:
            for declarator in field.declarators:
                field_info = {
                    'name': declarator.name,
                    'type': field.type.name
                }
                # 添加泛型信息（如果有）
                if hasattr(field.type, 'arguments') and field.type.arguments:
                    field_info['generic_type'] = [arg.type.name for arg in field.type.arguments]
                fields.append(field_info)
        return fields

    def _extract_entity_type(self, root) -> str:
        """从Mapper XML中提取实体类型"""
        # 1. 从resultMap中提取
        result_maps = root.findall('resultMap')
        if result_maps:
            return result_maps[0].get('type')
            
        # 2. 从insert语句的parameterType提取
        inserts = root.findall('insert')
        if inserts:
            return inserts[0].get('parameterType')
            
        # 3. 从namespace推测
        namespace = root.get('namespace')
        if namespace:
            # 通常mapper的namespace是entity包名+Mapper
            possible_entity = namespace.replace('mapper', 'entity').replace('Mapper', '')
            return possible_entity
            
        return None

    def get_training_pairs(self) -> List[Dict]:
        """获取训练数据对"""
        training_pairs = []
        
        for namespace, mapper_info in self.existing_mappers.items():
            entity_type = mapper_info['entity_type']
            if entity_type in self.entity_classes:
                entity_info = self.entity_classes[entity_type]
                training_pairs.append({
                    'entity': entity_info,
                    'mapper': mapper_info,
                    'interface': mapper_info.get('interface', {}),
                    'patterns': self.naming_patterns
                })
        
        print("\n=== 生成的训练数据对 ===")
        print(f"成功匹配的数据对数量: {len(training_pairs)}")
        for pair in training_pairs:
            print(f"\n实体类: {pair['entity']['name']}")
            print(f"对应的Mapper: {pair['mapper']['namespace']}")
            print(f"命名模式: {pair['patterns']}")
        
        return training_pairs