# -*- coding: utf-8 -*-
import codecs
from setuptools import find_packages, setup


setup(
    name="widgetastic.core",
    use_scm_version=True,
    author="Milan Falesnik",
    author_email="mfalesni@redhat.com",
    description='Making testing of UIs fantastic',
    long_description=codecs.open('README.rst', mode='r', encoding='utf-8').read(),
    license="Apache license",
    url="https://github.com/RedHatQE/widgetastic.core",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
        'cached_property',
        'selenium',
        'selenium-smart-locator',
        'wait_for',
    ],
    setup_requires=[
        'setuptools_scm',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
    ],
)
