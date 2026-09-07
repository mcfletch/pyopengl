import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('OpenGL.plugins').setLevel(logging.ERROR)


def fail_handler(*args, **named):
    raise RuntimeError("Should not have called this handler!")


logging.getLogger('OpenGL.plugins').addHandler(fail_handler)
from OpenGL.arrays import arraydatatype

dt = arraydatatype.GLuintArray
d = dt.zeros((3,))

print('OK')
