import unittest
import tempfile
import os
import zipfile
import sys
from unittest.mock import patch, MagicMock
if "/www/server/panel" not in sys.path:
    sys.path.append("/www/server/panel")

from mod.project.java.utils import get_jar_war_config, to_utf8, parse_application_yaml, TomCat


class TestJarWarConfig(unittest.TestCase):
    def setUp(self):
        # 创建测试用的zip文件
        self.test_jar = tempfile.NamedTemporaryFile(delete=False)
        self.test_jar_name = self.test_jar.name
        self.test_jar.close()

        # 创建一个包含application.yaml的zip文件
        with zipfile.ZipFile(self.test_jar_name, 'w') as jar:
            jar.writestr('application.yaml', 'spring:\n  datasource:\n    url: jdbc:mysql://localhost:3306/testdb')

        # 创建一个不包含application.yaml的zip文件
        self.test_jar_no_config = tempfile.NamedTemporaryFile(delete=False)
        self.test_jar_no_config_name = self.test_jar_no_config.name
        self.test_jar_no_config.close()

        with zipfile.ZipFile(self.test_jar_no_config_name, 'w') as jar:
            jar.writestr('README.txt', 'This is a test JAR without configuration')

        # 创建一个非zip文件
        self.test_non_zip = tempfile.NamedTemporaryFile(delete=False)
        self.test_non_zip_name = self.test_non_zip.name
        self.test_non_zip.close()

        # 创建一个不存在的文件路径
        self.test_non_existent = 'non_existent.jar'

    def tearDown(self):
        # 删除测试文件
        os.unlink(self.test_jar_name)
        os.unlink(self.test_jar_no_config_name)
        os.unlink(self.test_non_zip_name)

    def test_get_jar_war_config_with_valid_jar(self):
        # 测试有效的JAR文件
        result = get_jar_war_config(self.test_jar_name)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertIn('application.yaml', result[0][0])

    def test_get_jar_war_config_with_no_config(self):
        # 测试没有配置文件的JAR
        result = get_jar_war_config(self.test_jar_no_config_name)
        self.assertIsNone(result)

    def test_get_jar_war_config_with_non_zip(self):
        # 测试非ZIP文件
        result = get_jar_war_config(self.test_non_zip_name)
        self.assertIsNone(result)

    def test_get_jar_war_config_with_non_existent(self):
        # 测试不存在的文件
        result = get_jar_war_config(self.test_non_existent)
        self.assertIsNone(result)

    def test_to_utf8(self):
        # 测试转换为UTF-8
        byte_data = 'test'.encode('utf-8')
        file_data_list = [('test.txt', byte_data)]
        result = to_utf8(file_data_list)
        self.assertIsNotNone(result)
        self.assertEqual(result, [('test.txt', 'test')])

    def test_parse_application_yaml_valid(self):
        # 测试有效的YAML配置
        byte_data = 'spring:\n  datasource:\n    url: jdbc:mysql://localhost:3306/testdb'
        file_data_list = [('application.yaml', byte_data.encode('utf-8'))]
        result = parse_application_yaml(file_data_list)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertIn('application.yaml', result[0][0])
        self.assertIsInstance(result[0][1], dict)
        self.assertEqual(result[0][1]['spring']['datasource']['url'], 'jdbc:mysql://localhost:3306/testdb')

    def test_parse_application_yaml_invalid(self):
        # 测试无效的YAML配置
        invalid_byte_data = 'not --- a valid yaml'
        file_data_list = [('application.yaml', invalid_byte_data.encode('utf-8'))]
        result = parse_application_yaml(file_data_list)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 0)


class TestTomCat(unittest.TestCase):
    def setUp(self):
        self.tomcat_path = "/usr/local/bttomcat/tomcat10"
        self.tomcat = TomCat(self.tomcat_path)

    def test_jdk_path(self):
        self.assertEqual(self.tomcat.jdk_path, "/usr/local/btjdk/jdk8")

    def test_config_xml(self):
        self.assertIsNotNone(self.tomcat.config_xml)
        print(self.tomcat.config_xml)

    def test_save_config_xml(self):
        self.tomcat.add_host("taaaaa", "/tmp/aaaa")
        self.tomcat.add_host("taaaaa", "/tmp/aaaa")
        self.tomcat.add_host("tbbb", "/tmp/tbbb")
        self.assertEqual(self.tomcat.save_config_xml(), True)
        with open(self.tomcat_path + "/conf/server.xml", "r") as f:
            print(f.read())

        self.tomcat.remove_host("tbbb")
        self.assertEqual(self.tomcat.save_config_xml(), True)
        with open(self.tomcat_path + "/conf/server.xml", "r") as f:
            print(f.read())

    def test_status(self):
        print(self.tomcat.status())


if __name__ == '__main__':
    unittest.main()
