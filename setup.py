try:
    from setuptools import setup, Extension
except ImportError as ex:
    from distutils.core import setup, Extension
import struct
import os
import sys

pin_home = os.environ.get('PIN_HOME')
if not pin_home:
    print('Please set PIN_HOME environment variable; e.g.:')
    print('export PIN_HOME=/apps/BRM/portal/brmdev/webexBRM/opt/portal/7.5/')
    sys.exit(1)

if not os.path.isdir(pin_home):
    print('Cannot find the directory in $PIN_HOME. Please set it correctly; e.g.:')
    print('export PIN_HOME=/apps/BRM/portal/brmdev/webexBRM/opt/portal/7.5/')
    sys.exit(1)


bits = struct.calcsize("P") * 8
assert bits in (32, 64)

include_dirs = [
    os.path.join(pin_home, 'include')
]

libraries_32 = [
    'portal',
    'pcmext',
]

libraries_64 = [
    'portal64',
    'pcmext64',
]

if bits == 32:
    libraries = libraries_32
else:
    libraries = libraries_64

library_dirs = [
    os.path.join(pin_home, 'lib')
]

extra_objects = []

extra_compile_args = []
if bits == 32:
    extra_compile_args.append('-m32')

extra_link_args = []
if bits == 32:
    extra_link_args.append('-m32')


with open('README.md') as f:
    long_description = f.read()

__version__ = None
exec(open('pybrm/_version.py', 'r').read())

setup(
    name='pybrm',
    version=__version__,
    description="A Python library for Oracle BRM",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/mkmoisen/pybrm',
    author='Matthew Moisen',
    author_email='mmoisen@cisco.com',
    license='MIT',
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: C',
        'Operating System :: POSIX :: Linux',
        'Natural Language :: English',
    ],
    keywords='brm',
    project_urls={
        'Documentation': 'https://github.com/mkmoisen/pybrm',
        'Source': 'https://github.com/mkmoisen/pybrm',
    },
    python_requires='>=3.6',
    ext_modules=[
        Extension(
            'pybrm.cbrm', ['src/pybrm.c'],
            include_dirs=include_dirs,
            libraries=libraries,
            library_dirs=library_dirs,
            runtime_library_dirs=library_dirs,
            extra_objects=extra_objects,
            extra_compile_args=extra_compile_args,
            extra_link_args=extra_link_args,
        ),
    ],
    packages=['pybrm']
    )

