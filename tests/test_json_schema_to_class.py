import importlib.util
import json
import unittest
from pathlib import Path

import json_schema_to_class


def absolute_import(name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(name, str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MyTestCase(unittest.TestCase):
    def setUp(self):
        current_path: Path = Path(__file__).parent
        self.schema_path = current_path / 'test_schema.json'
        self.schema_path_2 = current_path / 'test_schema_2.json'
        self.output_path = current_path / 'build' / 'test_schema.py'

        with open(str(self.schema_path)) as f:
            self.test_schema = json.load(f)
        with open(str(self.schema_path_2)) as f:
            self.test_schema_2 = json.load(f)

    def test_basic(self):
        parser = json_schema_to_class.Parser()
        parser.parse(schema={
            'title': 'miss',
            'type': 'number',
            'default': 3.26
        })
        self.assertRaises(ValueError, parser.root.to_class_code)

    def test_definition(self):
        parser = json_schema_to_class.Parser()
        parser.parse(schema={
            'title': 'snow',
            '$ref': '#/definitions/miss',
            'definitions': {
                'miss': {
                    'type': 'number',
                    'default': 3.26
                }
            }
        })
        self.assertRaises(ValueError, parser.root.to_class_code)

    def test_array(self):
        parser = json_schema_to_class.Parser()
        parser.parse(schema={
            'title': 'days',
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'date': {
                        'type': 'integer'
                    }
                }
            }
        })

        code = parser.root.to_class_code()
        exec(code)
        self.assertTrue(True)

    def test_enum(self):
        def parse_empty_definition():
            parser = json_schema_to_class.Parser()
            parser.parse(schema={
                'title': 'days',
                'type': 'object',
                'properties': {
                    'mode': {
                        'enum': ['cosine', 'linear', 0]
                    }
                }
            })

        self.assertRaises(AssertionError, parse_empty_definition)

    def test_parse(self):
        def parse_empty_definition():
            parser = json_schema_to_class.Parser()
            parser.parse(schema={
                'title': 'days',
                'type': 'array',
                'items': {
                }
            })

        self.assertRaises(ValueError, parse_empty_definition)

    def test_to_structure(self):
        parser = json_schema_to_class.Parser()
        parser.parse(schema=self.test_schema)
        for name, definition in parser.definitions.items():
            self.assertIsNotNone(definition.to_json())
        parser.parse(schema=self.test_schema_2)

    def test_json_schema_to_class(self):
        json_schema_to_class.generate_file(schema_path=self.schema_path, output_path=self.output_path)
        module = absolute_import(name='generate', module_path=self.output_path)
        self.assertIsNotNone(module)

        values = [
            {
                "base_lr": None,
                "decay_factor": 0.99,
                "lr_decay": 0.1,
                "lr_mode": "cos",
                "target_lr": 0.0002,
                "milestones": [0.4, 0.7, 0.9],
                "warm_up": {
                    "start": 0.2,
                    "steps": 1024
                }
            }
        ]

        obj = getattr(module, 'LrSchedulerConfigs')(values=[{}])
        self.assertEqual(obj.items[0].warm_up.start, 0.0)

        obj = getattr(module, 'LrSchedulerConfigs')(values=values)
        self.assertEqual(obj.items[0].milestones, [0.4, 0.7, 0.9])
        self.assertEqual(obj.items[0].warm_up.start, 0.2)

        self.assertEqual(json_schema_to_class.to_json(obj), values)

    def test_generate_dir(self):
        json_schema_to_class.generate_dir(
            schema_dir=self.schema_path.parent,
            output_dir=self.output_path.parent
        )


if __name__ == '__main__':
    unittest.main()
