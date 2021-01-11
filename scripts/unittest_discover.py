import unittest
from os.path import dirname

test = unittest.TestLoader().discover(start_dir=dirname(dirname(__file__)))
runner = unittest.runner.TextTestRunner()
result = runner.run(test)
sys.exit(result.wasSuccessful())
