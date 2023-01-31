import os
import sys
import re
from setuptools import setup
from glob import glob

MIN_PYTHON = (2, 7)
if sys.version_info < MIN_PYTHON:
    sys.stderr.write("Python {}.{} or later is required\n".format(*MIN_PYTHON))
    sys.exit(1)


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


RE_VERSION = re.compile(r".*__version__ = '(.*?)'", re.S)

try:
    VERSION = RE_VERSION.match(
        read(os.path.join('make_profiler', '__init__.py'))).group(1)
except Exception:
    raise RuntimeError('Unable to determine version.')


setup(
    name='make-profiler',
    version=VERSION,
    author='Darafei Praliaskouski',
    author_email='komzpa@gojuno.com',
    maintainer='Alexander Verbitsky',
    maintainer_email='averbitsky@gojuno.com',
    description='Profiler for Makefiles',
    long_description=read('README.md'),
    keywords=['profiler', 'make', 'gnu-make'],
    url='https://github.com/gojuno/make-profiler',
    packages=['make_profiler'],
    test_suite='test',
    zip_safe=False,
    install_requires=(
        'more-itertools==2.4.1',
    ),
    entry_points={
        'console_scripts': [
            'profile_make_clean = make_profiler.cmd_clean:main',
            'profile_make = make_profiler.__main__:main',
            'profile_make_lint = make_profiler.lint_makefile:main',
            'profile_make_init_viewer = make_profiler.viewer_export:main'
        ]
    },
    data_files=[
        ('report', glob('make_profiler/report/*'))
    ],
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Utilities',
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
    ],
)
