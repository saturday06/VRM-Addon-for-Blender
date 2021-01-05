import os
import sys
import unittest

test = unittest.TestLoader().discover(
    start_dir=os.path.dirname(os.path.dirname(__file__)), top_level_dir="."
)
runner = unittest.runner.TextTestRunner()
result = runner.run(test)
sys.exit(result.wasSuccessful())
